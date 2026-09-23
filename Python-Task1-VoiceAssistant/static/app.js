let recognition = null;
let isListening = false;


// =========================================================
// ELEMENTS
// =========================================================

const voiceButton =
    document.getElementById("voiceButton");

const micIcon =
    document.getElementById("micIcon");

const voiceStatus =
    document.getElementById("voiceStatus");

const conversation =
    document.getElementById("conversation");

const stopSpeakingButton =
    document.getElementById("stopSpeaking");

const newConversationButton =
    document.getElementById("newConversation");

const welcomeGreeting =
    document.getElementById("welcomeGreeting");

const liveDate =
    document.getElementById("liveDate");

const liveTime =
    document.getElementById("liveTime");

const searchToggle =
    document.getElementById("searchToggle");

const searchBox =
    document.getElementById("searchBox");

const searchInput =
    document.getElementById("searchInput");

const searchButton =
    document.getElementById("searchButton");

const emailQuick =
    document.getElementById("emailQuick");

const emailPanel =
    document.getElementById("emailPanel");

const recipientInput =
    document.getElementById("recipient");

const subjectInput =
    document.getElementById("subject");

const emailBody =
    document.getElementById("emailBody");

const sendEmailButton =
    document.getElementById("sendEmail");

const emailStatus =
    document.getElementById("emailStatus");

const portfolioQuick =
    document.getElementById("portfolioQuick");

const createImageButton =
    document.getElementById("createImageButton");

const deepResearchButton =
    document.getElementById("deepResearchButton");

const openButton =
    document.getElementById("openButton");

const themeButton =
    document.getElementById("themeButton");


// =========================================================
// THEME SYSTEM
// =========================================================

const systemTheme =
    window.matchMedia(
        "(prefers-color-scheme: dark)"
    );


let currentTheme =
    localStorage.getItem(
        "voiceAssistantTheme"
    ) || "system";


function applyTheme(theme) {

    currentTheme =
        theme;


    if (theme === "system") {

        document.documentElement
            .removeAttribute(
                "data-theme"
            );

        themeButton.textContent =
            "◐";

        themeButton.title =
            "Theme: System";

        return;
    }


    document.documentElement
        .setAttribute(
            "data-theme",
            theme
        );


    if (theme === "light") {

        themeButton.textContent =
            "☀";

        themeButton.title =
            "Theme: Light";

    } else {

        themeButton.textContent =
            "☾";

        themeButton.title =
            "Theme: Dark";
    }
}


applyTheme(
    currentTheme
);


themeButton.addEventListener(
    "click",
    () => {

        let nextTheme;


        if (currentTheme === "system") {

            nextTheme = "light";

        } else if (
            currentTheme === "light"
        ) {

            nextTheme = "dark";

        } else {

            nextTheme = "system";
        }


        localStorage.setItem(
            "voiceAssistantTheme",
            nextTheme
        );


        applyTheme(
            nextTheme
        );
    }
);


// Follow system preference while in System mode
systemTheme.addEventListener(
    "change",
    () => {

        if (
            currentTheme === "system"
        ) {

            applyTheme(
                "system"
            );
        }
    }
);


// =========================================================
// GREETING
// =========================================================

function updateGreeting() {

    const hour =
        new Date().getHours();


    let greeting;


    if (
        hour >= 5 &&
        hour < 12
    ) {

        greeting =
            "Good morning";

    } else if (
        hour >= 12 &&
        hour < 17
    ) {

        greeting =
            "Good afternoon";

    } else {

        greeting =
            "Good evening";
    }


    welcomeGreeting.textContent =
        `Hello, ${greeting}`;
}


updateGreeting();


setInterval(
    updateGreeting,
    60000
);


// =========================================================
// LIVE DATE / TIME
// =========================================================

function updateDateTime() {

    const now =
        new Date();


    const dateFormatter =
        new Intl.DateTimeFormat(
            "en-US",
            {
                weekday:
                    "long",

                year:
                    "numeric",

                month:
                    "long",

                day:
                    "numeric"
            }
        );


    const timeFormatter =
        new Intl.DateTimeFormat(
            "en-US",
            {
                hour:
                    "numeric",

                minute:
                    "2-digit",

                second:
                    "2-digit",

                hour12:
                    true
            }
        );


    liveDate.textContent =
        dateFormatter.format(now);


    liveTime.textContent =
        timeFormatter.format(now);
}


updateDateTime();


setInterval(
    updateDateTime,
    1000
);


// =========================================================
// TEXT TO SPEECH
// =========================================================

function speak(text) {

    if (
        !("speechSynthesis" in window)
    ) {
        return;
    }


    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(
            text
        );


    utterance.lang =
        "en-IN";

    utterance.rate =
        0.95;

    utterance.pitch =
        1.0;

    utterance.volume =
        1.0;


    window.speechSynthesis.speak(
        utterance
    );
}


stopSpeakingButton.addEventListener(
    "click",
    () => {

        window.speechSynthesis.cancel();
    }
);


// =========================================================
// CONVERSATION
// =========================================================

function addMessage(
    text,
    type
) {

    const message =
        document.createElement(
            "div"
        );


    message.className =
        `message ${type}`;


    message.textContent =
        text;


    conversation.appendChild(
        message
    );


    message.scrollIntoView({
        behavior:
            "smooth",

        block:
            "nearest"
    });
}


// =========================================================
// LISTENING STATE
// =========================================================

function setListeningState(
    active
) {

    isListening =
        active;


    if (active) {

        voiceButton.classList.add(
            "active"
        );


        voiceStatus.classList.add(
            "listening"
        );


        voiceStatus.classList.remove(
            "error"
        );


        voiceStatus.textContent =
            "Listening...";


        micIcon.textContent =
            "🔴";

    } else {

        voiceButton.classList.remove(
            "active"
        );


        voiceStatus.classList.remove(
            "listening"
        );


        if (
            !voiceStatus.classList.contains(
                "error"
            )
        ) {

            voiceStatus.textContent =
                "Ready to listen";
        }


        micIcon.textContent =
            "🎙️";
    }
}


// =========================================================
// SPEECH ERROR
// =========================================================

function handleSpeechError() {

    setListeningState(
        false
    );


    voiceStatus.classList.add(
        "error"
    );


    voiceStatus.textContent =
        "I didn't understand. Please repeat.";


    const message =
        "I didn't understand. Please repeat.";


    addMessage(
        message,
        "assistant"
    );


    speak(
        message
    );


    setTimeout(
        () => {

            if (!isListening) {

                voiceStatus.classList.remove(
                    "error"
                );

                voiceStatus.textContent =
                    "Ready to listen";
            }

        },
        3000
    );
}


// =========================================================
// SPEECH RECOGNITION
// =========================================================

function createRecognition() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

        voiceStatus.classList.add(
            "error"
        );


        voiceStatus.textContent =
            "Voice recognition is not supported in this browser.";


        return null;
    }


    const recognizer =
        new SpeechRecognition();


    recognizer.lang =
        "en-IN";


    recognizer.continuous =
        false;


    recognizer.interimResults =
        false;


    recognizer.maxAlternatives =
        1;


    recognizer.onstart =
        () => {

            setListeningState(
                true
            );
        };


    recognizer.onresult =
        (event) => {

            const transcript =
                event.results[0][0]
                    .transcript
                    .trim();


            setListeningState(
                false
            );


            if (!transcript) {

                handleSpeechError();

                return;
            }


            addMessage(
                transcript,
                "user"
            );


            runCommand(
                transcript
            );
        };


    recognizer.onerror =
        (event) => {

            setListeningState(
                false
            );


            if (
                event.error ===
                "not-allowed"
            ) {

                voiceStatus.classList.add(
                    "error"
                );


                voiceStatus.textContent =
                    "Microphone permission is required.";


                speak(
                    "Please allow microphone permission and try again."
                );


                return;
            }


            handleSpeechError();
        };


    recognizer.onend =
        () => {

            setListeningState(
                false
            );
        };


    return recognizer;
}


recognition =
    createRecognition();


// =========================================================
// MICROPHONE
// =========================================================

voiceButton.addEventListener(
    "click",
    () => {

        if (!recognition) {

            handleSpeechError();

            return;
        }


        if (isListening) {

            recognition.stop();

            return;
        }


        try {

            window.speechSynthesis.cancel();

            recognition.start();

        } catch (error) {

            console.error(error);

            handleSpeechError();
        }
    }
);


// =========================================================
// COMMAND API
// =========================================================

async function runCommand(
    text
) {

    try {

        const response =
            await fetch(
                "/api/command",
                {
                    method:
                        "POST",

                    headers:
                        {
                            "Content-Type":
                                "application/json"
                        },

                    body:
                        JSON.stringify({
                            text:
                                text
                        })
                }
            );


        const data =
            await response.json();


        const message =
            data.message ||
            "I couldn't process that request.";


        // Answer appears above microphone
        addMessage(
            message,
            "assistant"
        );


        speak(
            message
        );


        // Search
        if (
            data.intent ===
                "search" &&
            data.url
        ) {

            setTimeout(
                () => {

                    window.open(
                        data.url,
                        "_blank",
                        "noopener,noreferrer"
                    );

                },
                500
            );
        }


        // Custom command
        if (
            data.intent ===
                "custom" &&
            data.url
        ) {

            setTimeout(
                () => {

                    window.open(
                        data.url,
                        "_blank",
                        "noopener,noreferrer"
                    );

                },
                500
            );
        }


        // Email
        if (
            data.intent ===
                "email" ||
            data.open_email
        ) {

            emailPanel.classList.remove(
                "hidden"
            );


            emailPanel.scrollIntoView({
                behavior:
                    "smooth",

                block:
                    "center"
            });
        }


        // Reminder
        if (
            data.intent ===
                "reminder" &&

            data.success &&

            Number.isFinite(
                data.seconds
            )
        ) {

            scheduleReminder(
                data.seconds,
                data.reminder_message
            );
        }

    } catch (error) {

        console.error(error);


        const message =
            "Something went wrong. Please try again.";


        addMessage(
            message,
            "assistant"
        );


        speak(
            message
        );
    }
}


// =========================================================
// WEB SEARCH
// =========================================================

searchToggle.addEventListener(
    "click",
    () => {

        searchBox.classList.toggle(
            "hidden"
        );


        if (
            !searchBox.classList.contains(
                "hidden"
            )
        ) {

            searchInput.focus();
        }
    }
);


function performSearch() {

    const query =
        searchInput.value.trim();


    if (!query) {

        searchInput.focus();

        return;
    }


    addMessage(
        query,
        "user"
    );


    const url =
        "https://www.google.com/search?q=" +
        encodeURIComponent(
            query
        );


    const message =
        `Searching the web for ${query}.`;


    addMessage(
        message,
        "assistant"
    );


    speak(
        message
    );


    setTimeout(
        () => {

            window.open(
                url,
                "_blank",
                "noopener,noreferrer"
            );

        },
        400
    );


    searchInput.value =
        "";


    searchBox.classList.add(
        "hidden"
    );
}


searchButton.addEventListener(
    "click",
    performSearch
);


searchInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter"
        ) {

            performSearch();
        }
    }
);


// =========================================================
// TOOL BUTTONS
// =========================================================

document
    .querySelectorAll(
        ".tool-button[data-command]"
    )
    .forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    const command =
                        button.dataset.command;


                    addMessage(
                        command,
                        "user"
                    );


                    runCommand(
                        command
                    );
                }
            );
        }
    );


// =========================================================
// CREATE IMAGE
// =========================================================

createImageButton.addEventListener(
    "click",
    () => {

        const prompt =
            window.prompt(
                "Describe the image you want to create:"
            );


        if (!prompt) {
            return;
        }


        addMessage(
            `Create image: ${prompt}`,
            "user"
        );


        const message =
            "Image creation is not connected to an image-generation API in this demo yet.";


        addMessage(
            message,
            "assistant"
        );


        speak(
            message
        );
    }
);


// =========================================================
// DEEP RESEARCH
// =========================================================

deepResearchButton.addEventListener(
    "click",
    () => {

        const topic =
            window.prompt(
                "What would you like to research?"
            );


        if (!topic) {
            return;
        }


        addMessage(
            `Deep Research: ${topic}`,
            "user"
        );


        const message =
            `Opening research results for ${topic}.`;


        addMessage(
            message,
            "assistant"
        );


        speak(
            message
        );


        const url =
            "https://www.google.com/search?q=" +
            encodeURIComponent(
                topic
            );


        setTimeout(
            () => {

                window.open(
                    url,
                    "_blank",
                    "noopener,noreferrer"
                );

            },
            500
        );
    }
);


// =========================================================
// OPEN
// =========================================================

openButton.addEventListener(
    "click",
    () => {

        const value =
            window.prompt(
                "Enter the website URL to open:"
            );


        if (!value) {
            return;
        }


        let url =
            value.trim();


        if (
            !url.startsWith("http://") &&
            !url.startsWith("https://")
        ) {

            url =
                "https://" +
                url;
        }


        try {

            const parsed =
                new URL(url);


            if (
                ![
                    "http:",
                    "https:"
                ].includes(
                    parsed.protocol
                )
            ) {

                throw new Error(
                    "Invalid URL"
                );
            }


            window.open(
                parsed.href,
                "_blank",
                "noopener,noreferrer"
            );

        } catch (error) {

            const message =
                "That doesn't look like a valid website address.";


            addMessage(
                message,
                "assistant"
            );


            speak(
                message
            );
        }
    }
);


// =========================================================
// EMAIL
// =========================================================

emailQuick.addEventListener(
    "click",
    () => {

        emailPanel.classList.remove(
            "hidden"
        );


        emailPanel.scrollIntoView({
            behavior:
                "smooth",

            block:
                "center"
        });
    }
);


sendEmailButton.addEventListener(
    "click",
    async () => {

        const recipient =
            recipientInput.value.trim();


        const subject =
            subjectInput.value.trim();


        const body =
            emailBody.value.trim();


        if (
            !recipient ||
            !body
        ) {

            emailStatus.textContent =
                "Please enter the recipient and message.";

            return;
        }


        emailStatus.textContent =
            "Sending email...";


        try {

            const response =
                await fetch(
                    "/api/email",
                    {
                        method:
                            "POST",

                        headers:
                            {
                                "Content-Type":
                                    "application/json"
                            },

                        body:
                            JSON.stringify({
                                recipient:
                                    recipient,

                                subject:
                                    subject,

                                body:
                                    body
                            })
                    }
                );


            const data =
                await response.json();


            emailStatus.textContent =
                data.message;


            addMessage(
                data.message,
                "assistant"
            );


            speak(
                data.message
            );

        } catch (error) {

            console.error(error);


            const message =
                "I couldn't send the email.";


            emailStatus.textContent =
                message;


            addMessage(
                message,
                "assistant"
            );


            speak(
                message
            );
        }
    }
);


// =========================================================
// PORTFOLIO
// =========================================================

portfolioQuick.addEventListener(
    "click",
    () => {

        const portfolioUrl =
            "https://github.com/";


        window.open(
            portfolioUrl,
            "_blank",
            "noopener,noreferrer"
        );
    }
);


// =========================================================
// REMINDER
// =========================================================

function scheduleReminder(
    seconds,
    reminderText
) {

    if (
        seconds <= 0
    ) {
        return;
    }


    setTimeout(
        () => {

            const message =
                `Reminder: ${reminderText}`;


            addMessage(
                message,
                "assistant"
            );


            speak(
                message
            );


            try {

                const AudioContext =
                    window.AudioContext ||
                    window.webkitAudioContext;


                if (!AudioContext) {
                    return;
                }


                const audioContext =
                    new AudioContext();


                const oscillator =
                    audioContext.createOscillator();


                const gainNode =
                    audioContext.createGain();


                oscillator.frequency.value =
                    880;


                oscillator.type =
                    "sine";


                gainNode.gain.value =
                    0.12;


                oscillator.connect(
                    gainNode
                );


                gainNode.connect(
                    audioContext.destination
                );


                oscillator.start();


                setTimeout(
                    () => {

                        oscillator.stop();

                        audioContext.close();

                    },
                    700
                );

            } catch (error) {

                console.log(
                    "Reminder sound unavailable:",
                    error
                );
            }

        },
        seconds * 1000
    );
}


// =========================================================
// NEW CONVERSATION
// =========================================================

newConversationButton.addEventListener(
    "click",
    () => {

        conversation.innerHTML =
            "";


        searchBox.classList.add(
            "hidden"
        );


        emailPanel.classList.add(
            "hidden"
        );


        searchInput.value =
            "";


        recipientInput.value =
            "";


        subjectInput.value =
            "";


        emailBody.value =
            "";


        emailStatus.textContent =
            "";


        window.speechSynthesis.cancel();


        if (isListening) {

            try {

                recognition.stop();

            } catch (error) {

                console.log(error);
            }
        }


        voiceStatus.classList.remove(
            "error",
            "listening"
        );


        voiceStatus.textContent =
            "Ready to listen";


        updateGreeting();

        updateDateTime();
    }
);