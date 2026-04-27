const ChannelManager = {
    init(channel) {
        window.channelObject = channel.objects.channelObject;
        window.channelObject.ready = true;

        console.log = function(...args) {
            if (window.channelObject) {
                const message = args.reduce((acc, arg) => 
                    acc + ' ' + (typeof arg === 'object' ? JSON.stringify(arg) : String(arg)), '');
                window.channelObject.handle_log(message);
            }
        };
    }
};

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function displayError(message) {
    Logger.error('UI', 'Error displayed to user', { message });
    const errorContainer = document.getElementById("errorContainer");
    errorContainer.textContent = message;
    errorContainer.style.display = "block";
    document.getElementById("loadingIndicator").style.display = "none";
}