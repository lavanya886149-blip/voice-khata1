const startBtn = document.getElementById("startBtn");

const statusText = document.getElementById("status");

const recognizedText = document.getElementById("recognizedText");

const resultText = document.getElementById("result");

const language = document.getElementById("language");


// BROWSER SPEECH RECOGNITION

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

let recognition;

if (SpeechRecognition) {

    recognition = new SpeechRecognition();

    recognition.continuous = false;

    recognition.interimResults = false;

    recognition.maxAlternatives = 1;

    recognition.onstart = function() {

        statusText.innerText = "🎤 Listening... Speak now";

        startBtn.innerText = "🔴 Listening...";

        startBtn.classList.add("recording");

        resultText.innerText = "";

    };


    recognition.onresult = async function(event) {

        const text = event.results[0][0].transcript;

        recognizedText.innerText = text;

        statusText.innerText = "Processing your speech...";

        await processVoice(text);

    };


    recognition.onerror = function(event) {

        statusText.innerText =
            "Voice error: " + event.error;

        startBtn.innerText = "🎤 Start Speaking";

        startBtn.classList.remove("recording");

    };


    recognition.onend = function() {

        startBtn.innerText = "🎤 Start Speaking";

        startBtn.classList.remove("recording");

    };

} else {

    statusText.innerText =
        "Speech recognition is not supported. Please use Google Chrome.";

}


// START MICROPHONE

startBtn.addEventListener("click", function() {

    if (!recognition) {
        alert("Please open this website in Google Chrome.");
        return;
    }

    recognition.lang = language.value;

    try {

        recognition.start();

    } catch(error) {

        statusText.innerText =
            "Please wait and try again.";

    }

});


// PROCESS VOICE

async function processVoice(text) {

    try {

        const response = await fetch("/process_voice", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                text: text
            })

        });

        const data = await response.json();

        if (data.success) {

            resultText.innerText =
                "✅ " + data.message +
                " | " + data.type +
                " | ₹" + data.amount;

            statusText.innerText = "Transaction saved!";

            loadDashboard();

        } else {

            resultText.innerText =
                "⚠️ " + data.message;

            statusText.innerText =
                "Please try speaking again.";

        }

    } catch(error) {

        resultText.innerText =
            "Server connection failed.";

    }

}


// ADD MANUAL TRANSACTION

document.getElementById("addBtn").addEventListener("click", async function() {

    const amount = document.getElementById("amount").value;

    const description =
        document.getElementById("description").value;

    const type = document.getElementById("type").value;

    if (!amount || Number(amount) <= 0) {

        alert("Please enter a valid amount");

        return;

    }

    const response = await fetch("/add", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            amount: amount,
            description: description,
            type: type
        })

    });

    const data = await response.json();

    alert(data.message);

    if (data.success) {

        document.getElementById("amount").value = "";

        document.getElementById("description").value = "";

        loadDashboard();

    }

});


// LOAD DASHBOARD

async function loadDashboard() {

    try {

        const response = await fetch("/summary");

        const data = await response.json();

        document.getElementById("income").innerText =
            "₹" + Number(data.income).toLocaleString("en-IN");

        document.getElementById("expense").innerText =
            "₹" + Number(data.expense).toLocaleString("en-IN");

        document.getElementById("balance").innerText =
            "₹" + Number(data.balance).toLocaleString("en-IN");


        const list = document.getElementById("transactionList");

        list.innerHTML = "";

        data.transactions.forEach(function(item) {

            const row = document.createElement("tr");

            const values = [
                item.date,
                item.description,
                item.type,
                "₹" + Number(item.amount).toLocaleString("en-IN")
            ];

            values.forEach(function(value) {

                const cell = document.createElement("td");

                cell.textContent = value;

                row.appendChild(cell);

            });

            list.appendChild(row);

        });

    } catch(error) {

        console.log("Dashboard loading error:", error);

    }

}


// CLEAR HISTORY

document.getElementById("clearBtn").addEventListener("click", async function() {

    if (!confirm("Are you sure you want to delete all transactions?")) {
        return;
    }

    const response = await fetch("/clear", {
        method: "POST"
    });

    const data = await response.json();

    alert(data.message);

    loadDashboard();

});


// LOAD DATA WHEN PAGE OPENS

loadDashboard();