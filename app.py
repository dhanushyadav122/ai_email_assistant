from flask import Flask, render_template, request
import requests
import json
import smtplib
from email.mime.text import MIMEText
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Gmail credentials
YOUR_EMAIL = "dhanuyadav29@gmail.com"
YOUR_APP_PASSWORD = "xzrg beec jons bffr"
app_key = "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"  # <-- replace with your OpenRouter key

# ---------- Sentiment Function ----------
def analyze_sentiment(text):
    try:
        headers = {
            "Authorization": f"Bearer {app_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a sentiment analysis expert. Respond only with Positive, Negative, or Neutral."},
                {"role": "user", "content": text}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Unknown ({str(e)})"

# ---------- Home Page ----------
@app.route("/", methods=["GET", "POST"])
def index():
    email_to = ""
    email_subject = ""
    send_status = ""
    suggestion = ""
    auto_reply = ""
    tone = ""
    language = ""
    mail_type = ""
    sentiment = ""

    if request.method == "POST":
        email_to = request.form['email_to']
        email_subject = request.form['subject']
        body_idea = request.form['body']
        tone = request.form.get('tone', 'friendly')
        language = request.form.get('language', 'english')
        mail_type = request.form.get('mail_type', 'personal')
        send_email = request.form.get('send_email')

        prompt = f"Write a {tone} {mail_type} email in {language} to {email_to}.\nSubject: {email_subject}\nContent: {body_idea}"

        headers = {"Authorization": f"Bearer {app_key}", "Content-Type": "application/json"}
        payload = {"model": "openai/gpt-3.5-turbo",
                   "messages": [{"role": "system", "content": "You are a helpful email assistant."},
                                {"role": "user", "content": prompt}]}
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                     headers=headers, json=payload)
            response.raise_for_status()
            suggestion = response.json()['choices'][0]['message']['content']
        except Exception as e:
            suggestion = f"❌ AI request failed: {str(e)}"

        sentiment = analyze_sentiment(suggestion)

        conn = sqlite3.connect('emails.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS email_history 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, recipient TEXT,
                      subject TEXT, body TEXT, timestamp TEXT, sentiment TEXT)""")
        c.execute("INSERT INTO email_history (type, recipient, subject, body, timestamp, sentiment) VALUES (?, ?, ?, ?, ?, ?)",
                  ("generated", email_to, email_subject, suggestion, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sentiment))
        conn.commit()
        conn.close()

        if send_email and suggestion:
            try:
                msg = MIMEText(suggestion)
                msg['Subject'] = email_subject
                msg['From'] = YOUR_EMAIL
                msg['To'] = email_to

                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(YOUR_EMAIL, YOUR_APP_PASSWORD)
                server.sendmail(YOUR_EMAIL, email_to, msg.as_string())
                server.quit()
                send_status = "😈 Devil, email sent successfully!"
            except Exception as e:
                send_status = f"❌ Failed to send email: {str(e)}"

    return render_template("index.html", suggestion=suggestion,
                           email_to=email_to, email_subject=email_subject,
                           send_status=send_status, tone=tone, language=language,
                           mail_type=mail_type, auto_reply=auto_reply)

# ---------- Auto Reply ----------
@app.route("/auto_reply", methods=["POST"])
def auto_reply():
    incoming_email = request.form['incoming_email']
    tone = request.form.get('tone', 'friendly')

    prompt = f"Write a {tone} reply for this email: {incoming_email}"

    headers = {"Authorization": f"Bearer {app_key}", "Content-Type": "application/json"}
    payload = {"model": "openai/gpt-3.5-turbo",
               "messages": [{"role": "system", "content": "You are an email auto-reply assistant."},
                            {"role": "user", "content": prompt}]}
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
    except Exception as e:
        reply = f"❌ AI request failed completely: {str(e)}"

    sentiment = analyze_sentiment(reply)

    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS email_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, recipient TEXT,
                  subject TEXT, body TEXT, timestamp TEXT, sentiment TEXT)""")
    c.execute("INSERT INTO email_history (type, recipient, subject, body, timestamp, sentiment) VALUES (?, ?, ?, ?, ?, ?)",
              ("auto_reply", "N/A", "Auto Reply", reply, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sentiment))
    conn.commit()
    conn.close()

    return render_template("index.html", auto_reply=reply)

# ---------- History ----------
@app.route("/history")
def history():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute("SELECT * FROM email_history")
    rows = c.fetchall()
    conn.close()
    return render_template("history.html", rows=rows)

@app.route("/clear_history", methods=["POST"])
def clear_history():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute("DELETE FROM email_history")
    conn.commit()
    conn.close()
    return render_template("history.html", rows=[])

if __name__ == "__main__":
    app.run(debug=True)
