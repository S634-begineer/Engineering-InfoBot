const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");//user input store from chatbox 
const sendBtn = document.getElementById("send-btn");

let step = 0;
let userData = {};
let currentPath = "";
// Flag to check if we are asking about another city
let isCheckingAnotherCity = false;

//a function that shows a bot msg on chatscreen
const sendBotMessage = (message) => {
  const msg = document.createElement("div");
  msg.classList.add("message", "bot-message", "mb-2", "p-2", "bg-light", "rounded");
  msg.innerHTML = message;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
};

//a function that shows a user msg on chatscreen 
const sendUserMessage = (message) => {
  const msg = document.createElement("div");
  msg.classList.add("message", "user-message", "text-end", "mb-2", "p-2", "bg-primary", "text-white", "rounded");
  msg.textContent = message;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
};
//first greeting msg 
sendBotMessage("👋 Hi there! What's your name?");

sendBtn.addEventListener("click", () => {
  const input = userInput.value.trim();
  if (input === "") return;
  sendUserMessage(input);
  userInput.value = "";
  handleResponse(input);
});

function handleResponse(input) {
  // --- LOGIC FOR CHECKING ANOTHER CITY ---
  if (isCheckingAnotherCity) {
    const response = input.toLowerCase();
    isCheckingAnotherCity = false; // Reset flag

    if (response === "yes" || response === "y") {
      sendBotMessage(`Great, ${userData.name}! You want to check another city. Please enter the new city name:`);
      step = 1; // Jump back to the city input step
      return;
    } else if (response === "no" || response === "n") {
      sendBotMessage("Thank you for using the college eligibility checker! Feel free to reload if you want to start a new profile.");
      userInput.disabled = true; // Disable input
      sendBtn.disabled = true; // Disable button
      return;
    } else {
      isCheckingAnotherCity = true; // Ask again if input is invalid
      sendBotMessage("Please enter **Yes** or **No**.");
      return;
    }
  }
  // ---------------------------------------------

  switch (step) {
    case 0:
      userData.name = input;
      sendBotMessage(`Nice to meet you, ${userData.name}! In which city do you want to take admission?`);
      break;

    case 1:
      userData.city = input.toLowerCase();
      
      //  FIX: If education data exists, skip to summary (checking another city flow)
      if (userData.education) {
        sendBotMessage(`Checking eligibility for **${userData.city.toUpperCase()}** with your existing profile...`);
        showSummary();
        step = 8; 
        return; // Skip step++ below
      }

      // Initial flow: ask for education
      sendBotMessage("What is your education background — 12th or Diploma?");
      break;

    case 2:
      currentPath = input.toLowerCase();
      if (currentPath === "12th" || currentPath === "diploma") {
        userData.education = currentPath;
        sendBotMessage("Which branch do you want to take admission in? (Computer / IT / Mechanical / Electrical / Civil)");
      } else {
        sendBotMessage("Please enter a valid option: 12th or Diploma.");
        step--;
      }
      break;

    case 3:
      userData.branch = input.toLowerCase();

      if (userData.education === "diploma") {
        sendBotMessage("Please enter your Diploma percentage:");
      } else {
        sendBotMessage("Please enter your 12th percentage:");
      }
      break;

    case 4:
      userData.percentage = parseFloat(input);

      // Stop immediately if percentage is 0
      if (userData.percentage === 0) {
        if (userData.education === "diploma") {
          sendBotMessage("⚠️ You have failed in Diploma. Cannot provide college list.");
        } else {
          sendBotMessage("⚠️ You have failed in 12th. Cannot provide college list.");
        }
        step = -1; 
        return; 
      }

      if (userData.education === "12th") {
        sendBotMessage("Which entrance exam have you given? (JEE / CET / None)");
      } else {
        sendBotMessage("Please select your category (Open / OBC / SC / ST / EWS):");
        step++; // Skip exam step
      }
      break;

    case 5:
      userData.examType = input.toLowerCase();

      if (userData.examType === "jee") {
        sendBotMessage("Please enter your JEE score:");
      } else if (userData.examType === "cet") {
        sendBotMessage("Please enter your CET score:");
      } else if (userData.examType === "none") {
        userData.exam_score = 0;
        sendBotMessage("Please select your category (Open / OBC / SC / ST / EWS):");
        step++;
      } else {
        sendBotMessage("Please enter valid: JEE / CET / None");
        step--;
      }
      break;

    case 6:
      if (userData.education === "diploma") {
        userData.category = input.toLowerCase();
        showSummary();
        step = 8; 
        return;
      }

      if (userData.education === "12th" && userData.examType !== "none") {
        userData.exam_score = parseFloat(input);

        // Stop if exam score is 0
        if (userData.exam_score === 0) {
          sendBotMessage(`⚠️ Invalid ${userData.examType.toUpperCase()} score! Cannot provide college list.`);
          step = -1;
          return;
        }
      }

      sendBotMessage("Please select your category (Open / OBC / SC / ST / EWS):");
      break;

    case 7:
      userData.category = input.toLowerCase();
      showSummary();
      step = 8; 
      return;

    case 8:
      step--;
      break;
  }
  step++;
}

//provide list of colleges received from backend 
function showSummary() {
  sendBotMessage("✅ Thank you! Please wait while we check your college eligibility...");

  fetch("http://127.0.0.1:5000/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      percentage: parseFloat(userData.percentage),
      exam_score: parseFloat(userData.exam_score) || 0,
      city: userData.city.trim(),
      branch: userData.branch.trim(),
      category: userData.category // Pass category to backend
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      setTimeout(() => {
        if (Array.isArray(data.college)) {
          sendBotMessage(`🎓 Based on your profile for **${userData.city.toUpperCase()}**, here are the college recommendations (Ranked by Model Prediction):`);
          data.college.forEach((c) => sendBotMessage(`• ${c}`));
        } else {
          sendBotMessage(`🎓 ${data.college}`);
        }
        if (data.ai_message && data.ai_message !== "undefined") {
          sendBotMessage(`💬 ${data.ai_message}`);
        }

        // Ask if user wants to check another city
        sendBotMessage("---"); 
        sendBotMessage(`Do you want to check for colleges in another city with the same profile (**${userData.education}**, **${userData.branch}**, **${userData.percentage}%** etc.)? (**Yes/No**)`);
        isCheckingAnotherCity = true; 
        step = 8; 
      }, 1000);
    })
    .catch((err) => {
      console.error(err);
      sendBotMessage("⚠️ Sorry, something went wrong while checking eligibility.");
    });
}
