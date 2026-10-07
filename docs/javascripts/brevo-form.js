/**
 * Load Brevo form assets when #sib-form is present.
 * Re-runs on Material Instant Navigation via document$.
 */
(function () {
  const SIB_STYLE = "https://sibforms.com/forms/end-form/build/sib-styles.css";
  const SIB_SCRIPT = "https://sibforms.com/forms/end-form/build/main.js";
  // Brevo’s embed still uses g-recaptcha markup for Turnstile sitekeys (0x4AAAAA…).
  // Load Turnstile in reCAPTCHA compatibility mode so grecaptcha.render works.
  const TURNSTILE_SCRIPT =
    "https://challenges.cloudflare.com/turnstile/v0/api.js?compat=recaptcha&render=explicit";

  window.handleCaptchaResponse = function handleCaptchaResponse() {
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

  function renderCaptcha() {
    const captcha = document.getElementById("sib-captcha");
    if (!captcha || typeof window.grecaptcha === "undefined") {
      return;
    }
    const ready = window.grecaptcha.ready || ((callback) => callback());
    ready(() => {
      if (captcha.querySelector("iframe, textarea")) {
        return;
      }
      try {
        window.grecaptcha.render(captcha, {
          sitekey: captcha.dataset.sitekey,
          callback: window.handleCaptchaResponse,
        });
      } catch (error) {
        // Widget may already be bound after Instant Navigation reuse.
        console.debug("Brevo captcha render skipped:", error);
      }
    });
  }

  async function initBrevoForm() {
    if (!document.getElementById("sib-form")) {
      return;
    }
    configureBrevo();
    ensureStylesheet();
    try {
      await loadExternalScript(TURNSTILE_SCRIPT, "data-brevo-turnstile");
      renderCaptcha();
      await loadBrevoMain();
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
