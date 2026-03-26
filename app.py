from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
os.makedirs("uploads", exist_ok=True)
from utils.pdf_reader import extract_text_from_pdf
from utils.ocr_reader import extract_text_from_image
from utils.ai_analyzer import analyze_contract
import json
import requests
from utils.fairness import calculate_fairness
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from flask import request, jsonify, session
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -----------------------
# Database Model
# -----------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------
# Routes
# -----------------------

@app.route('/')
def landing():
    return render_template("landing.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email,password=password).first()

        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid login")

    return render_template("login.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user = User(name=name,email=email,password=password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please login.")
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", name=current_user.name)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))
import json

@app.route("/upload", methods=["GET","POST"])
@login_required
def upload():

    if request.method == "POST":

        file = request.files["contract"]
        filepath = os.path.join("uploads", file.filename)
        file.save(filepath)

        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(filepath)
        else:
            text = extract_text_from_image(filepath)

        ai_result = analyze_contract(text)

        # 🔥 CLEAN JSON (IMPORTANT)
        cleaned = ai_result.replace("```json", "").replace("```", "").strip()

        try:
            json_data = json.loads(cleaned)
        except:
            json_data = {}

        session["contract_data"] = json_data
        
        return render_template("result.html",
                               text=cleaned,
                               data=json_data)

    return render_template("upload.html")



@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.form.get("data")

    # Convert string → dict
    json_data = json.loads(data)

    analysis = calculate_fairness(json_data)

    return render_template(
        "analysis.html",
        analysis=analysis
    )

@app.route("/result")
@login_required
def result():

    global extracted_text

    return render_template("result.html", text=extracted_text)

    

@app.route("/vin", methods=["GET", "POST"])
def vin_lookup():
    result = None

    if request.method == "POST":
        vin = request.form["vin"]

        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"

        response = requests.get(url)
        data = response.json()

        result = data["Results"][0]

    return render_template("vin.html", result=result)
    

from flask import request, jsonify, session
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route("/chat_api", methods=["POST"])
def chat_api():
    try:
        user_message = request.json.get("message")

        print("User:", user_message)

        # 🔹 Get contract data
        contract_data = session.get("contract_data", {})

        if not contract_data:
            return jsonify({"reply": "⚠️ Please upload a contract first."})

        # 🔥 NEW: Calculate fairness
        fairness = calculate_fairness(contract_data)

        print("Fairness:", fairness)

        # 🔥 Risk-based warning (optional but powerful)
        if fairness["risk"] in ["DANGER", "HIGH RISK"]:
            warning = "⚠️ This contract is HIGH RISK. Be cautious."
        else:
            warning = ""

        # 🔥 UPDATED PROMPT
        prompt = f"""
You are an expert car lease assistant.

Talk like a smart human advisor — not like a report.

IMPORTANT RULES:
- Use fairness score and risk level to guide your answer
- If risk is HIGH/DANGER → clearly warn the user
- NEVER say "fairly standard" if there are red flags
- If contract is risky → explain why
- Answer ONLY what the user asks

STYLE:
- Natural conversation (like ChatGPT)
- Friendly but professional
- Simple language
- 3–5 lines max
- No headings or rigid structure

---

Contract Data:
{contract_data}

Fairness Score: {fairness["score"]}
Risk Level: {fairness["risk"]}
Red Flags: {fairness["red_flags"]}

{warning}

---

User Question:
{user_message}
"""

        # 🔹 Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a smart financial and negotiation advisor."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"reply": "⚠️ Error: " + str(e)})
    
@app.route("/chat")
def chat():
    return render_template("chat.html", name=session.get("name"))


# -----------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)