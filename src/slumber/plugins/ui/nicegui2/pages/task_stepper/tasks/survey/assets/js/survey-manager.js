function initializeSurvey(surveyJson) {
    Logger.info('Survey', 'Initialization started', { config: surveyJson.title });
    
    const survey = new Survey.Model(surveyJson);
    survey.applyTheme(SurveyTheme.SharpDark);

    // Store survey instance globally so locale can be updated dynamically
    currentSurveyInstance = survey;

    // Set initial locale based on value provided by Python
    const currentLocale = getCurrentLocale();
    survey.locale = currentLocale;
    Logger.info('Survey', 'Locale set to:', currentLocale);
    
    survey.pages.forEach((page, pageIndex) => {
        Logger.info('Survey', `Processing page ${pageIndex + 1}/${survey.pages.length}`, {
            pageTitle: page.title,
            elementCount: page.elements.length
        });
        
        page.elements.forEach((element, elementIndex) => {
            Logger.info('Survey', 'Element processed', {
                pageIndex,
                elementIndex,
                type: element.getType(),
                name: element.name,
                isRegistered: Survey.ElementFactory.Instance.getAllTypes().includes(element.getType())
            });
        });
    });

    survey.onComplete.add((sender) => {
        Logger.info('Survey', 'Survey completed', { 
            questionCount: Object.keys(sender.data).length 
        });
        window.channelObject?.handle_survey_submission(JSON.stringify(sender.data));
    });

    const converter = markdownit({
        html: true // Support HTML tags in the source (unsafe, see documentation)
    });
    survey.onTextMarkdown.add((_, options) => {
        // Convert Markdown to HTML
        let str = converter.renderInline(options.text);
        options.html = str;
    });

    return survey;
}

// Global variable to store current survey instance for dynamic locale changes
let currentSurveyInstance = null;

// Get current locale from value injected by Python (see widget.py)
function getCurrentLocale() {
    try {
        // This is set from Python before the survey is loaded
        return window.surveyLocale || 'default';
    } catch (error) {
        Logger.error('Survey', 'Failed to get current locale', error);
        return 'default';
    }
}

// Change the survey locale dynamically from Python or JS
function setLocale(locale) {
    if (currentSurveyInstance) {
        currentSurveyInstance.locale = locale;
        Logger.info('Survey', 'Locale changed to:', locale);
    } else {
        Logger.warning('Survey', 'No survey instance available to change locale');
    }
}