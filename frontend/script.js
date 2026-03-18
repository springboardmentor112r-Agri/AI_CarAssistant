function goBack() {
    // Hide all sections and remove active states
    ['ai', 'chat', 'risk', 'summary'].forEach(function(s) {
        var el = document.getElementById('section-' + s);
        if (el) el.style.display = 'none';
        var nav = document.getElementById('nav-' + s);
        if (nav) nav.classList.remove('active');
    });
    // Show the hero
    var hero = document.getElementById('introScreen');
    if (hero) hero.style.display = 'flex';
}

function showSection(name) {
    // Hide hero
    const hero = document.getElementById('introScreen');
    if (hero) hero.style.display = 'none';

    // Hide all sections
    ['ai', 'chat', 'risk', 'summary'].forEach(function(s) {
        var el = document.getElementById('section-' + s);
        if (el) el.style.display = 'none';
        var nav = document.getElementById('nav-' + s);
        if (nav) nav.classList.remove('active');
    });

    // Show the selected section (block for content sections, flex for placeholders)
    var target = document.getElementById('section-' + name);
    if (target) target.style.display = (name === 'risk' || name === 'summary') ? 'flex' : 'block';

    // Mark active sidebar item
    var navItem = document.getElementById('nav-' + name);
    if (navItem) navItem.classList.add('active');
}

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const result = document.getElementById("result");
    const loading = document.getElementById("loading");
    const successBanner = document.getElementById("uploadSuccessBanner");
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
    if (successBanner) successBanner.style.display = "none";
    if (chatBox) chatBox.innerHTML = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/extract-lease/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        loading.style.display = "none";
        result.textContent = formatOutput(data);

        // Prime the chat with a welcome message and show the Go-to-Chat banner
        if (chatBox) chatBox.innerHTML = '<div class="message bot-message"><span>Hi! I can answer any questions about this lease. What would you like to know?</span></div>';
        const chatInput = document.getElementById("chatInput");
        if (chatInput) chatInput.value = "";
        if (successBanner) successBanner.style.display = "flex";

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

function handleLogin(event) {
    if (event) event.preventDefault();
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
    window.location.href = "index.html";
}

function handleSignup(event) {
    if (event) event.preventDefault();
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
    window.location.href = "index.html";
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

/**
 * Generate Lease Risk Score based on extracted data
 */
async function generateRiskScore() {
    const riskResults = document.getElementById("risk-results");
    const riskEmpty = document.getElementById("risk-empty");
    const riskLoading = document.getElementById("risk-loading");
    const generateBtn = document.getElementById("risk-generate-btn");
    const regenerateBtn = document.getElementById("risk-regenerate-btn");
    
    // Show loading state
    riskEmpty.style.display = "none";
    riskResults.style.display = "none";
    riskLoading.style.display = "flex";
    if (generateBtn) generateBtn.disabled = true;
    if (regenerateBtn) regenerateBtn.disabled = true;
    
    try {
        const response = await fetch("http://127.0.0.1:8000/calculate-risk/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });
        
        const data = await response.json();
        riskLoading.style.display = "none";
        
        if (data.status === "error") {
            // Show empty state with error message
            const emptyMessage = riskEmpty.querySelector(".risk-empty-message");
            if (emptyMessage) {
                emptyMessage.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <p>${data.message}</p>
                    <button class="btn btn-primary" onclick="showSection('ai')">Upload Document</button>
                `;
            }
            riskEmpty.style.display = "flex";
            if (generateBtn) generateBtn.style.display = "none";
            if (regenerateBtn) regenerateBtn.style.display = "none";
        } else {
            // Display risk results
            displayRiskScore(data);
            riskResults.style.display = "grid";
            if (generateBtn) generateBtn.style.display = "none";
            if (regenerateBtn) regenerateBtn.style.display = "block";
        }
        
    } catch (error) {
        riskLoading.style.display = "none";
        const emptyMessage = riskEmpty.querySelector(".risk-empty-message p");
        if (emptyMessage) {
            emptyMessage.textContent = "Error: " + error.message;
        }
        riskEmpty.style.display = "flex";
    } finally {
        if (generateBtn) generateBtn.disabled = false;
        if (regenerateBtn) regenerateBtn.disabled = false;
    }
}

/**
 * Display the risk score and breakdown on the page
 */
function displayRiskScore(data) {
    const riskScore = data.risk_score || 0;
    const riskLevel = data.risk_level || "Unknown";
    const breakdown = data.breakdown || {};
    const missingFields = data.missing_fields || [];
    const notes = data.notes || "";
    
    const badge = document.getElementById("risk-score-badge");
    const scoreNumber = document.getElementById("risk-score-number");
    const scoreLabel = document.getElementById("risk-score-label");
    const scoreNotes = document.getElementById("risk-score-notes");
    
    // Update risk badge styling based on level
    badge.className = "risk-badge " + riskLevel.toLowerCase();
    scoreNumber.textContent = riskScore;
    scoreLabel.textContent = riskLevel + " Risk";
    
    // Format notes as separate lines
    if (notes) {
        const noteLines = notes.split("\n");
        scoreNotes.innerHTML = noteLines.map(line => {
            return `<div class="risk-note-line">${line}</div>`;
        }).join("");
    }
    
    // Update factor breakdown
    updateRiskFactor("termination", breakdown["Early Termination Fee"]);
    updateRiskFactor("mileage", breakdown["Allowed Mileage"]);
    updateRiskFactor("excess-fee", breakdown["Excess Mileage Fee"]);
    updateRiskFactor("payment", breakdown["Monthly Payment"]);
    updateRiskFactor("interest", breakdown["Interest Rate"]);
    
    // Show missing fields alert if any
    const missingFieldsDiv = document.getElementById("risk-missing-fields");
    const missingList = document.getElementById("risk-missing-list");
    if (missingFields.length > 0) {
        missingList.textContent = "Please clarify: " + missingFields.join(", ");
        missingFieldsDiv.style.display = "flex";
    } else {
        missingFieldsDiv.style.display = "none";
    }
}

/**
 * Update a single risk factor display
 */
function updateRiskFactor(factorId, factorData) {
    if (!factorData) return;
    
    const score = factorData.score || 0;
    const severity = factorData.severity || "Unknown";
    const value = factorData.value || "N/A";
    
    const valueEl = document.getElementById(`risk-factor-${factorId}-value`);
    const barEl = document.getElementById(`risk-factor-${factorId}-bar`);
    const scoreEl = document.getElementById(`risk-factor-${factorId}-score`);
    const severityEl = document.getElementById(`risk-factor-${factorId}-severity`);
    
    if (valueEl) valueEl.textContent = value;
    if (barEl) {
        barEl.style.width = score + "%";
        barEl.className = "risk-factor-bar-fill " + severity.toLowerCase();
    }
    if (scoreEl) scoreEl.textContent = score + "/100";
    if (severityEl) {
        severityEl.textContent = severity;
        severityEl.className = "risk-severity risk-severity-" + severity.toLowerCase();
    }
}

/**
 * Toggle risk breakdown visibility
 */
function toggleRiskBreakdown() {
    const content = document.getElementById("risk-breakdown-content");
    const btn = document.querySelector(".risk-toggle-btn");
    
    if (content.style.display === "grid") {
        content.style.display = "none";
        if (btn) btn.classList.add("collapsed");
    } else {
        content.style.display = "grid";
        if (btn) btn.classList.remove("collapsed");
    }
}

/**
 * Initialize risk section when extract is successful
 */
function initializeRiskSection(fromUpload = false) {
    const riskEmpty = document.getElementById("risk-empty");
    const generateBtn = document.getElementById("risk-generate-btn");
    
    if (riskEmpty) riskEmpty.style.display = "flex";
    if (generateBtn) generateBtn.style.display = "block";
}

// Update uploadFile to initialize risk section
const originalUploadFile = uploadFile;
window.uploadFile = async function() {
    const result = await originalUploadFile.apply(this, arguments);
    // Initialize risk section after successful upload
    setTimeout(() => {
        initializeRiskSection(true);
        initializeSummarySection(true);
    }, 500);
    return result;
};

/**
 * Generate Simple Contract Summary
 */
async function generateSummary() {
    const summaryResults = document.getElementById("summary-results");
    const summaryEmpty = document.getElementById("summary-empty");
    const summaryLoading = document.getElementById("summary-loading");
    const generateBtn = document.getElementById("summary-generate-btn");
    const regenerateBtn = document.getElementById("summary-regenerate-btn");
    
    // Show loading state
    summaryEmpty.style.display = "none";
    summaryResults.style.display = "none";
    summaryLoading.style.display = "flex";
    if (generateBtn) generateBtn.disabled = true;
    if (regenerateBtn) regenerateBtn.disabled = true;
    
    try {
        const response = await fetch("http://127.0.0.1:8000/generate-summary/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });
        
        const data = await response.json();
        summaryLoading.style.display = "none";
        
        if (data.status === "error") {
            // Show empty state with error message
            const emptyMessage = summaryEmpty.querySelector(".summary-empty-message");
            if (emptyMessage) {
                emptyMessage.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <p>${data.message}</p>
                    <button class="btn btn-primary" onclick="showSection('ai')">Upload Document</button>
                `;
            }
            summaryEmpty.style.display = "flex";
            if (generateBtn) generateBtn.style.display = "none";
            if (regenerateBtn) regenerateBtn.style.display = "none";
        } else {
            // Display summary results
            displaySummary(data);
            summaryResults.style.display = "block";
            if (generateBtn) generateBtn.style.display = "none";
            if (regenerateBtn) regenerateBtn.style.display = "block";
        }
        
    } catch (error) {
        summaryLoading.style.display = "none";
        const emptyMessage = summaryEmpty.querySelector(".summary-empty-message p");
        if (emptyMessage) {
            emptyMessage.textContent = "Error: " + error.message;
        }
        summaryEmpty.style.display = "flex";
    } finally {
        if (generateBtn) generateBtn.disabled = false;
        if (regenerateBtn) regenerateBtn.disabled = false;
    }
}

/**
 * Display the summary on the page
 */
function displaySummary(data) {
    const summaryText = document.getElementById("summary-text");
    
    if (data.summary) {
        // Format the summary text with proper line breaks
        const formattedSummary = data.summary
            .split('\n')
            .map(line => {
                if (line.trim() === '') {
                    return '<div class="summary-paragraph-break"></div>';
                }
                // Check if line starts with ** (heading)
                if (line.includes('**')) {
                    return '<div class="summary-section-heading">' + 
                        line.replace(/\*\*/g, '').trim() + 
                        '</div>';
                }
                // Check if line starts with - (bullet point)
                if (line.trim().startsWith('-')) {
                    return '<div class="summary-bullet">' + 
                        line.replace(/^-\s*/, '').trim() + 
                        '</div>';
                }
                return '<div class="summary-paragraph">' + line.trim() + '</div>';
            })
            .join('');
        
        summaryText.innerHTML = formattedSummary;
    }
}

/**
 * Initialize summary section when extract is successful
 */
function initializeSummarySection(fromUpload = false) {
    const summaryEmpty = document.getElementById("summary-empty");
    const generateBtn = document.getElementById("summary-generate-btn");
    
    if (summaryEmpty) summaryEmpty.style.display = "flex";
    if (generateBtn) generateBtn.style.display = "block";
}
