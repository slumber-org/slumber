/**
 * Load Brevo form assets when #sib-form is present.
 * Re-runs on Material Instant Navigation via document$.
 *
 * Matches Brevo’s Cloudflare Turnstile embed: cf-turnstile markup, alias
 * window.grecaptcha = window.turnstile, and captchaChange for validation.
 */
(function () {
  const SIB_STYLE = "https://sibforms.com/forms/end-form/build/sib-styles.css";
  const SIB_SCRIPT = "https://sibforms.com/forms/end-form/build/main.js";
  const TURNSTILE_SCRIPT =
    "https://challenges.cloudflare.com/turnstile/v0/api.js";

  function setBrevoCaptchaToken(token) {
    const form = document.getElementById("sib-form");
    if (!form) {
      return;
    }
    let input = form.querySelector(
      'textarea[name="g-recaptcha-response"], input[name="g-recaptcha-response"]',
    );
    if (!input) {
      input = document.createElement("textarea");
      input.name = "g-recaptcha-response";
      input.setAttribute("aria-hidden", "true");
      input.tabIndex = -1;
      input.style.display = "none";
      form.appendChild(input);
    }
    input.value = token || "";
  }

  function aliasGreCaptcha() {
    if (window.turnstile) {
      window.grecaptcha = window.turnstile;
    }
  }

  window.handleCaptchaResponse = function handleCaptchaResponse(token) {
    // Brevo’s embed aliases grecaptcha to turnstile after a successful challenge.
    aliasGreCaptcha();
    setBrevoCaptchaToken(token);
    const captcha = document.getElementById("sib-captcha");
    if (captcha) {
      captcha.dispatchEvent(new Event("captchaChange"));
    }
  };

  function configureBrevo() {
    window.REQUIRED_CODE_ERROR_MESSAGE = "Please choose a country code";
    window.LOCALE = "en";
    window.EMAIL_INVALID_MESSAGE = window.SMS_INVALID_MESSAGE =
      "Please check your email address and try again.";
    window.REQUIRED_ERROR_MESSAGE = "Please complete this field. ";
    window.GENERIC_INVALID_MESSAGE =
      "Please check your email address and try again.";
    window.INVALID_NUMBER = "Please check your email address and try again.";
    window.INVALID_DATE = "Please enter a valid date";
    window.REQUIRED_MULTISELECT_MESSAGE = "Please select at least 1 option";
    window.translation = {
      common: {
        selectedList: "{quantity} list selected",
        selectedLists: "{quantity} lists selected",
        selectedOption: "{quantity} selected",
        selectedOptions: "{quantity} selected",
      },
    };
    window.AUTOHIDE = Boolean(0);
  }

  function ensureStylesheet() {
    if (document.querySelector(`link[data-brevo-styles="${SIB_STYLE}"]`)) {
      return;
    }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = SIB_STYLE;
    link.dataset.brevoStyles = SIB_STYLE;
    document.head.appendChild(link);
  }

  function loadExternalScript(src, marker) {
    return new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[${marker}]`);
      if (existing) {
        if (existing.dataset.loaded === "true") {
          resolve();
          return;
        }
        existing.addEventListener("load", () => resolve(), { once: true });
        existing.addEventListener(
          "error",
          () => reject(new Error(`Failed to load ${src}`)),
          { once: true },
        );
        return;
      }
      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.defer = true;
      script.setAttribute(marker, "true");
      script.onload = () => {
        script.dataset.loaded = "true";
        resolve();
      };
      script.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.body.appendChild(script);
    });
  }

  function loadBrevoMain() {
    const previous = document.querySelector("script[data-brevo-main]");
    if (previous) {
      previous.remove();
    }
    return loadExternalScript(SIB_SCRIPT, "data-brevo-main");
  }

  function waitForTurnstile() {
    return new Promise((resolve, reject) => {
      const started = Date.now();
      const poll = () => {
        if (window.turnstile && typeof window.turnstile.render === "function") {
          aliasGreCaptcha();
          if (typeof window.turnstile.ready === "function") {
            window.turnstile.ready(() => resolve(window.turnstile));
          } else {
            resolve(window.turnstile);
          }
          return;
        }
        if (Date.now() - started > 10000) {
          reject(new Error("Timed out waiting for Turnstile"));
          return;
        }
        window.setTimeout(poll, 50);
      };
      poll();
    });
  }

  function captchaTheme() {
    return document.body.getAttribute("data-md-color-scheme") === "slate"
      ? "dark"
      : "light";
  }

  async function renderCaptcha() {
    const captcha = document.getElementById("sib-captcha");
    if (!captcha) {
      return;
    }

    const turnstile = await waitForTurnstile();
    const previousId = captcha.dataset.turnstileWidgetId;
    if (previousId) {
      try {
        turnstile.remove(previousId);
      } catch {
        // Widget may already be gone after Instant Navigation.
      }
      delete captcha.dataset.turnstileWidgetId;
    }

    // Fresh container for Instant Navigation re-entry.
    if (captcha.querySelector("iframe, textarea, input")) {
      captcha.replaceChildren();
    }
    setBrevoCaptchaToken("");

    const widgetId = turnstile.render(captcha, {
      sitekey: captcha.getAttribute("data-sitekey"),
      theme: captchaTheme(),
      language: captcha.getAttribute("data-language") || "en",
      callback: window.handleCaptchaResponse,
      "expired-callback": () => {
        setBrevoCaptchaToken("");
        captcha.dispatchEvent(new Event("captchaChange"));
      },
      "error-callback": () => {
        setBrevoCaptchaToken("");
      },
    });
    if (widgetId != null) {
      captcha.dataset.turnstileWidgetId = String(widgetId);
    }
  }

  async function initBrevoForm() {
    if (!document.getElementById("sib-form")) {
      return;
    }
    configureBrevo();
    ensureStylesheet();
    try {
      // Match Brevo footer order: form runtime, then Turnstile.
      await loadBrevoMain();
      await loadExternalScript(TURNSTILE_SCRIPT, "data-brevo-turnstile");
      await renderCaptcha();
    } catch (error) {
      console.error(error);
    }
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(initBrevoForm);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBrevoForm);
  } else {
    initBrevoForm();
  }
})();
