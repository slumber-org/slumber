Survey.Serializer.addClass("voicetext", [
    { name: "title", type: "string" },
    { name: "name", type: "string" }
], null, "question");

Survey.JsonObject.metaData.addClass("voicetext", [], null, "empty");

Survey.CustomWidgetCollection.Instance.add({
    name: "voicetext",
    title: "Voice or Text Response",
    widgetIsLoaded: function() {
        Logger.info('Survey', 'Widget loaded');
        return true;
    },
    isFit: function(question) {
        return question.getType() === "voicetext";
    },
    htmlTemplate: `
        <div class="sd-question__content">
            <div class="custom-switch-container">
                <span class="custom-switch-text-left">🖋️ Text</span>
                <label class="custom-switch">
                    <input type="checkbox" class="custom-switch-input">
                    <span class="custom-switch-slider"></span>
                </label>
                <span class="custom-switch-text-right">🎤 Voice</span>
            </div>
            <div id="textSection" class="sd-question__content-wrapper" style="display: none; margin-top: 16px;">
                <textarea class="sd-input sd-comment" rows="4" placeholder="Type your response here..."></textarea>
            </div>
            <div id="voiceSection" class="sd-question__content-wrapper" style="display: none; margin-top: 16px;">
                <div class="sd-action-bar">
                    <button id="startRecord" class="sd-btn sd-btn--primary">🎤 Start Recording</button>
                    <button id="stopRecord" class="sd-btn sd-btn--secondary" disabled>⏹ Stop Recording</button>
                </div>
                <div id="recordingStatus" class="recording-status"></div>
                <audio id="audioPlayback" controls style="display: none; margin-top: 10px; width: 100%;"></audio>
            </div>
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
            .custom-switch-container {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 10px;
            }
            .custom-switch {
                position: relative;
                width: 50px;
                height: 24px;
                display: inline-block;
                cursor: pointer;
            }
            .custom-switch-input {
                opacity: 0;
                width: 0;
                height: 0;
            }
            .custom-switch-slider {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: #ccc;
                border-radius: 50px;
                transition: 0.3s;
            }
            .custom-switch-slider::before {
                content: "";
                position: absolute;
                height: 18px;
                width: 18px;
                left: 3px;
                bottom: 3px;
                background-color: white;
                border-radius: 50%;
                transition: 0.3s;
            }
            .custom-switch-input:checked + .custom-switch-slider {
                background-color: #4CAF50;
            }
            .custom-switch-input:checked + .custom-switch-slider::before {
                transform: translateX(26px);
            }
            .custom-switch-text-left,
            .custom-switch-text-right {
                transition: 0.3s;
                color: #E5E9F0;  /* Light color for dark theme */
            }
            .custom-switch-input:checked ~ .custom-switch-text-left {
                color: #4C566A;  /* Darker color for inactive state */
            }
            .custom-switch-input:not(:checked) ~ .custom-switch-text-right {
                color: #4C566A;  /* Darker color for inactive state */
            }
        </style>
    `,
    afterRender: function(question, el) {
        const toggleInput = el.querySelector('.custom-switch-input');
        const textSection = el.querySelector("#textSection");
        const voiceSection = el.querySelector("#voiceSection");
        const textArea = el.querySelector("textarea");
        const startButton = el.querySelector("#startRecord");
        const stopButton = el.querySelector("#stopRecord");
        const audio = el.querySelector("#audioPlayback");
        const status = el.querySelector("#recordingStatus");
        let mediaRecorder;
        let chunks = [];
        let recordingTimer;
        let elapsedTime = 0;

        textSection.style.display = "block";

        // Restore previous value if it exists
        if (question.value) {
            if (question.value.type === 'text') {
                textArea.value = question.value.content;
                toggleInput.checked = false;
                textSection.style.display = "block";
                voiceSection.style.display = "none";
            } else if (question.value.type === 'audio') {
                audio.src = question.value.content;
                audio.style.display = "block";
                toggleInput.checked = true;
                textSection.style.display = "none";
                voiceSection.style.display = "block";
                status.className = "recording-status complete";
                status.innerHTML = "✅ Recording complete";
            }
        }

        // Check if it's in preview mode
        if (question.isPreview) {
            // In preview mode, make the text area read-only and hide the recording buttons
            textArea.readOnly = true;
            startButton.disabled = true;
            stopButton.disabled = true;
        }

        toggleInput.onchange = (e) => {
            if (!e.target.checked) {
                textSection.style.display = "block";
                voiceSection.style.display = "none";
            } else {
                voiceSection.style.display = "block";
                textSection.style.display = "none";
            }
        };

        textArea.onchange = function() {
            question.value = {
                type: 'text',
                content: this.value
            };
        };

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
