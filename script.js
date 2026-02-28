async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const result = document.getElementById("result");
    const loading = document.getElementById("loading");
    const chatSection = document.getElementById("chatSection");
    const chatBox = document.getElementById("chatBox");

    if (!fileInput.files.length) {
        alert("Please select a PDF or image file.");
        return;
    }

    const file = fileInput.files[0];
    const allowedTypes = new Set([
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/bmp",
        "image/tiff"
    ]);

    if (!allowedTypes.has(file.type)) {
        alert("Unsupported file type. Upload a PDF or an image (PNG/JPG/WebP/BMP/TIFF).");
        fileInput.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    loading.style.display = "flex";
    result.textContent = "";
    chatSection.style.display = "none";
    chatBox.innerHTML = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/extract-lease/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        loading.style.display = "none";
        result.textContent = formatOutput(data);
        
        // Show chat section after successful extraction
        chatSection.style.display = "block";
        chatBox.innerHTML = '<div class="message bot-message"><span>Hi! I can answer any questions about this lease. What would you like to know?</span></div>';
        document.getElementById("chatInput").value = "";

    } catch (error) {
        loading.style.display = "none";
        result.textContent = "Error: " + error;
    }
}

function showIntroPanel(panel) {
    const loginPanel = document.getElementById("loginPanel");
    const signupPanel = document.getElementById("signupPanel");
    const loginTab = document.getElementById("loginTab");
    const signupTab = document.getElementById("signupTab");

    if (!loginPanel || !signupPanel || !loginTab || !signupTab) return;

    const isLogin = panel === "login";
    loginPanel.style.display = isLogin ? "grid" : "none";
    signupPanel.style.display = isLogin ? "none" : "grid";
    loginTab.classList.toggle("active", isLogin);
    signupTab.classList.toggle("active", !isLogin);
}

function showApp() {
    const introScreen = document.getElementById("introScreen");
    const appPage = document.getElementById("appPage");
    if (introScreen && appPage) {
        introScreen.style.display = "none";
        appPage.style.display = "grid";
        return;
    }

    window.location.href = "index.html";
}

function handleLogin() {
    const emailInput = document.getElementById("loginEmail");
    const passwordInput = document.getElementById("loginPassword");
    const errorBox = document.getElementById("loginError");
    if (!emailInput || !passwordInput || !errorBox) return;

    errorBox.textContent = "";

    const emailResult = validateEmail(emailInput.value);
    if (!emailResult.isValid) {
        errorBox.textContent = emailResult.message;
        return;
    }

    const passwordResult = validatePassword(passwordInput.value);
    if (!passwordResult.isValid) {
        errorBox.textContent = passwordResult.message;
        return;
    }

    emailInput.value = emailResult.normalized;
    showApp();
}

function handleSignup() {
    const nameInput = document.getElementById("signupName");
    const emailInput = document.getElementById("signupEmail");
    const passwordInput = document.getElementById("signupPassword");
    const errorBox = document.getElementById("signupError");
    if (!nameInput || !emailInput || !passwordInput || !errorBox) return;

    errorBox.textContent = "";

    const emailResult = validateEmail(emailInput.value);
    if (!emailResult.isValid) {
        errorBox.textContent = emailResult.message;
        return;
    }

    const passwordResult = validatePassword(passwordInput.value);
    if (!passwordResult.isValid) {
        errorBox.textContent = passwordResult.message;
        return;
    }

    emailInput.value = emailResult.normalized;
    showApp();
}

function validateEmail(rawEmail) {
    // Normalize and enforce the 254 character limit per RFC recommendations.
    const trimmed = String(rawEmail || "").trim();
    if (!trimmed) {
        return { isValid: false, message: "Email is required." };
    }

    if (trimmed.length > 254) {
        return { isValid: false, message: "Email must be 254 characters or fewer." };
    }

    if (/\s/.test(trimmed)) {
        return { isValid: false, message: "Email cannot contain spaces." };
    }

    const atCount = (trimmed.match(/@/g) || []).length;
    if (atCount !== 1) {
        return { isValid: false, message: "Email must contain exactly one @ symbol." };
    }

    // Production-grade email regex with a strict domain and TLD check.
    const emailRegex = /^(?=.{1,254}$)(?=.{1,64}@)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63})$/;
    if (!emailRegex.test(trimmed)) {
        return { isValid: false, message: "Enter a valid email address (example: name@domain.com)." };
    }

    return { isValid: true, normalized: trimmed.toLowerCase() };
}

function validatePassword(rawPassword) {
    // Enforce length and character rules without leaking internal details.
    const password = String(rawPassword || "");
    if (!password) {
        return { isValid: false, message: "Password is required." };
    }

    if (password.length < 8 || password.length > 128) {
        return { isValid: false, message: "Password must be between 8 and 128 characters." };
    }

    if (/\s/.test(password)) {
        return { isValid: false, message: "Password cannot contain spaces." };
    }

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$/;
    if (!passwordRegex.test(password)) {
        return {
            isValid: false,
            message: "Password must include uppercase, lowercase, number, and special character (@$!%*?&)."
        };
    }

    return { isValid: true };
}

function peekPassword(inputId, shouldShow) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.type = shouldShow ? "text" : "password";
}

function logout() {
    const introScreen = document.getElementById("introScreen");
    const appPage = document.getElementById("appPage");
    const result = document.getElementById("result");
    const loading = document.getElementById("loading");
    const chatSection = document.getElementById("chatSection");
    const chatBox = document.getElementById("chatBox");
    const fileInput = document.getElementById("fileInput");

    if (introScreen) introScreen.style.display = "block";
    if (appPage) appPage.style.display = "none";
    if (loading) loading.style.display = "none";
    if (result) result.textContent = "";
    if (chatSection) chatSection.style.display = "none";
    if (chatBox) chatBox.innerHTML = "";
    if (fileInput) fileInput.value = "";
    if (introScreen && appPage) {
        showIntroPanel("login");
        return;
    }

    window.location.href = "auth.html";
}

function formatOutput(data) {
    if (!data || typeof data !== "object") {
        return String(data || "No data returned.");
    }

    if (data.error) {
        return "Error: " + data.error;
    }

    const lines = [];
    for (const [key, value] of Object.entries(data)) {
        if (Array.isArray(value)) {
            const items = value.length ? value.join(", ") : "None";
            lines.push(`${key}: ${items}`);
        } else if (value && typeof value === "object") {
            lines.push(`${key}:`);
            for (const [innerKey, innerValue] of Object.entries(value)) {
                lines.push(`  - ${innerKey}: ${innerValue ?? "N/A"}`);
            }
        } else {
            lines.push(`${key}: ${value ?? "N/A"}`);
        }
    }

    return lines.join("\n");
}

async function sendChat() {
    const chatInput = document.getElementById("chatInput");
    const chatBox = document.getElementById("chatBox");
    const question = chatInput.value.trim();

    if (!question) return;

    // Add user message
    const userMsg = document.createElement("div");
    userMsg.className = "message user-message";
    userMsg.innerHTML = `<span>${question}</span>`;
    chatBox.appendChild(userMsg);

    // Clear input
    chatInput.value = "";

    // Add loading indicator
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "message bot-message loading";
    loadingMsg.id = "chat-loading";
    loadingMsg.innerHTML = `<span><div class="chat-spinner"></div></span>`;
    chatBox.appendChild(loadingMsg);

    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch("http://127.0.0.1:8000/ask/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(question)
        });

        const data = await response.json();
        
        // Remove loading indicator
        const loadingElement = document.getElementById("chat-loading");
        if (loadingElement) loadingElement.remove();

        // Add bot response
        const botMsg = document.createElement("div");
        botMsg.className = "message bot-message";
        botMsg.innerHTML = `<span>${data.answer || data.message}</span>`;
        chatBox.appendChild(botMsg);

        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        // Remove loading indicator
        const loadingElement = document.getElementById("chat-loading");
        if (loadingElement) loadingElement.remove();

        // Add error message
        const errorMsg = document.createElement("div");
        errorMsg.className = "message bot-message";
        errorMsg.innerHTML = `<span>Error: ${error.message}</span>`;
        chatBox.appendChild(errorMsg);
    }
}

function handleChatKeyPress(event) {
    if (event.key === "Enter") {
        sendChat();
    }
}
