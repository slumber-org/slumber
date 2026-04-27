Survey.Serializer.addClass("voice", [
    { name: "title", type: "string" },
    { name: "name", type: "string" }
], null, "question");

Survey.JsonObject.metaData.addClass("voice", [], null, "empty");

Survey.CustomWidgetCollection.Instance.add({
    name: "voice",
    title: "Voice Recording",
    widgetIsLoaded: function() {
        Logger.info('Survey', 'Widget loaded');
        return true;
    },
    isFit: function(question) {
        return question.getType() === "voice";
    },
    htmlTemplate: `
        <div class="sd-question__content">
            <div class="sd-action-bar">
                <button id="startRecord" class="sd-btn sd-btn--primary">🎤 Start Recording</button>
                <button id="stopRecord" class="sd-btn sd-btn--secondary" disabled>⏹ Stop Recording</button>
            </div>
            <div id="recordingStatus" class="recording-status"></div>
            <audio id="audioPlayback" controls style="display: none; margin-top: 10px; width: 100%;"></audio>
        </div>
        <style>
            .recording-status {
                margin-top: 10px;
                font-weight: bold;
                font-size: 14px;
                text-align: center;
            }
            .recording-status.recording {
                color: red;
                animation: blink 1s infinite;
            }
            .recording-status.complete {
                color: green;
            }
            @keyframes blink {
                50% { opacity: 0.5; }
            }
            .sd-action-bar {
                margin-bottom: 16px;
                text-align: center;
            }
        </style>
    `,
    afterRender: function(question, el) {
        const startButton = el.querySelector("#startRecord");
        const stopButton = el.querySelector("#stopRecord");
        const audio = el.querySelector("#audioPlayback");
        const status = el.querySelector("#recordingStatus");
        let mediaRecorder;
        let chunks = [];
        let recordingTimer;
        let elapsedTime = 0;

        // Check if it's in preview mode
        if (question.isPreview) {
            startButton.disabled = true;
            stopButton.disabled = true;
        }

        startButton.onclick = async () => {
            try {
                chunks = [];
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus',
                    bitsPerSecond: 32000
                });

                mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
                mediaRecorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const audioURL = URL.createObjectURL(blob);
                    audio.src = audioURL;
                    audio.style.display = "block";

                    const reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = () => {
                        question.value = {
                            type: 'audio',
                            content: reader.result
                        };
                    };
                };

                mediaRecorder.start();
                startButton.disabled = true;
                stopButton.disabled = false;
                audio.style.display = "none";

                // Reset status
                elapsedTime = 0;
                status.className = "recording-status recording";
                status.innerHTML = `🔴 Recording... 0s`;

                // Start recording timer
                recordingTimer = setInterval(() => {
                    elapsedTime++;
                    status.innerHTML = `🔴 Recording... ${elapsedTime}s`;
                }, 1000);

            } catch (error) {
                console.log("Recording error:", error);
                status.className = "recording-status";
                status.innerHTML = `⚠️ Error: Could not access microphone`;
            }
        };

        stopButton.onclick = () => {
            clearInterval(recordingTimer);
            mediaRecorder.stop();
            startButton.disabled = false;
            stopButton.disabled = true;

            // Update UI to show recording is complete
            status.className = "recording-status complete";
            status.innerHTML = `✅ Recording complete (${elapsedTime}s)`;

            const tracks = mediaRecorder.stream.getTracks();
            tracks.forEach(track => track.stop());
        };
    }
});
