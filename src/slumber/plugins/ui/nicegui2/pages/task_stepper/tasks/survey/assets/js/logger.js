const Logger = {
    info: function(component, message, data = null) {
        const logMessage = {
            level: 'INFO',
            component,
            message,
            data,
            timestamp: new Date().toISOString()
        };
        window.channelObject?.handle_log(JSON.stringify(logMessage));
    },
    error: function(component, message, error = null) {
        const logMessage = {
            level: 'ERROR',
            component,
            message,
            error: error?.toString(),
            stack: error?.stack,
            timestamp: new Date().toISOString()
        };
        window.channelObject?.handle_error(JSON.stringify(logMessage));
    }
};