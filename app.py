from flask import Flask, render_template, request, jsonify
import sqlite3
import re
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

DB_NAME = Path(__file__).resolve().parent / "voice_khata.db"


# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE TABLE
def initialize_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS voice_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# DETECT TRANSACTION TYPE
def detect_type(text):

    text = text.lower()

    income_words = [
        "income", "received", "salary", "earned",
        "ಆದಾಯ", "ಸಂಬಳ", "ಬಂದಿತು", "ಸಿಕ್ಕಿತು",
        "आय", "मिला", "कमाई", "वेतन",
        "வருமானம்", "சம்பளம்", "கிடைத்தது",
        "ఆదాయం", "జీతం", "వచ్చింది",
        "വരുമാനം", "ശമ്പളം",
        "उत्पन्न", "पगार",
        "আয়", "বেতন",
        "આવક", "પગાર",
        "آمدنی"
    ]

    expense_words = [
        "expense", "spent", "paid", "bought",
        "ಖರ್ಚು", "ವೆಚ್ಚ", "ಕೊಟ್ಟೆ",
        "खर्च", "खरीदा", "भुगतान",
        "செலவு", "செலவழித்தேன்",
        "ఖర్చు", "చెల్లించాను",
        "ചെലവ്", "ചിലവാക്കി",
        "खर्च", "खरेदी",
        "খরচ", "ব্যয়",
        "ખર્ચ", "ચૂકવ્યું",
        "خرچ"
    ]

    if any(word in text for word in income_words):
        return "Income"

    if any(word in text for word in expense_words):
        return "Expense"

    return "Unknown"


# EXTRACT AMOUNT
def extract_amount(text):
    numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', text)

    if numbers:
        return float(numbers[0].replace(",", ""))

    return 0


# ADD TRANSACTION
@app.route("/add", methods=["POST"])
def add_transaction():

    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid amount"
        }), 400

    transaction_type = data.get("type", "")
    description = data.get("description", "")

    if amount <= 0:
        return jsonify({
            "success": False,
            "message": "Enter a valid amount"
        }), 400

    if transaction_type not in ["Income", "Expense"]:
        return jsonify({
            "success": False,
            "message": "Invalid transaction type"
        }), 400

    conn = get_db()

    conn.execute("""
        INSERT INTO voice_transactions
        (type, amount, description, date)
        VALUES (?, ?, ?, ?)
    """, (
        transaction_type,
        amount,
        description,
        datetime.now().strftime("%d-%m-%Y %H:%M")
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Transaction saved successfully!"
    })


# VOICE TEXT PROCESSING
@app.route("/process_voice", methods=["POST"])
def process_voice():

    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()

    if not text:
        return jsonify({
            "success": False,
            "message": "No voice text received"
        }), 400

    amount = extract_amount(text)
    transaction_type = detect_type(text)

    if amount <= 0:
        return jsonify({
            "success": False,
            "message": "Amount not detected. Please speak the amount in digits."
        })

    if transaction_type == "Unknown":
        return jsonify({
            "success": False,
            "message": "Please mention income or expense."
        })

    # Save automatically
    conn = get_db()

    conn.execute("""
        INSERT INTO voice_transactions
        (type, amount, description, date)
        VALUES (?, ?, ?, ?)
    """, (
        transaction_type,
        amount,
        text,
        datetime.now().strftime("%d-%m-%Y %H:%M")
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "text": text,
        "amount": amount,
        "type": transaction_type,
        "message": "Transaction saved successfully!"
    })


# DASHBOARD SUMMARY
@app.route("/summary")
def summary():

    conn = get_db()

    income = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM voice_transactions WHERE type='Income'
    """).fetchone()[0]

    expense = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM voice_transactions WHERE type='Expense'
    """).fetchone()[0]

    transactions = conn.execute("""
        SELECT * FROM voice_transactions
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify({
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "transactions": [dict(t) for t in transactions]
    })


# TRANSACTION HISTORY
@app.route("/history")
def history():

    conn = get_db()

    records = conn.execute("""
        SELECT * FROM voice_transactions
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in records])


# CLEAR TRANSACTIONS
@app.route("/clear", methods=["POST"])
def clear():

    conn = get_db()

    conn.execute("DELETE FROM voice_transactions")

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "History cleared successfully"
    })


# RUN APPLICATION
initialize_database()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )