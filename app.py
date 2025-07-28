from flask import Flask, render_template, request
import requests
import json
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

# Gmail credentials
YOUR_EMAIL = "dhanuyadav29@gmail.com"
YOUR_APP_PASSWORD = "xzrg beec jons bffr"
app_key = os.environ.get("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")  # API key from Render environment

@app.route("/", methods=["GET", "POST"])
def index():
    email_to = ""
    email_subject = ""
    send_status = ""
    suggestion = ""
    tone = ""
    language = ""
    mail_type = ""

    if request.method == "POST":
        email_to = request.form['email_to']
        email_subject = request.form['subject']
        body_idea = request.form['body']
        tone = request.form.get('tone', 'friendly')
        language = request.form.get('language', 'english')
        mail_type = request.form.get('mail_type', 'personal')
        send_email = request.form.get('send_email')

        # Generate prompt
        prompt = f"""Write a {tone} {mail_type} email in {language} to {email_to}.
Subject: {email_subject}
Content: {body_idea}"""

        # Call AI API (OpenRouter)
        headers = {
            "Authorization": f"Bearer {app_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral/mistral-7b-instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful email assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                     headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            suggestion = response.json()['choices'][0]['message']['content']
        except Exception as e:
            suggestion = f"❌ AI request failed: {str(e)}"

        # Send the email if user checked the box
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

    return render_template("index.html",
                           suggestion=suggestion,
                           email_to=email_to,
                           email_subject=email_subject,
                           send_status=send_status,
                           tone=tone,
                           language=language,
                           mail_type=mail_type)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
