import smtplib 
from email.message import EmailMessage
from core.email_config import em

def send_email_with_alerts(email:str, alerts: list):
    msg = EmailMessage()
    msg['From'] = em.Login
    msg['To'] = email
    msg['Subject'] = "Rate alert"
    msg.set_content(f'''Your Target rate was got 
                    {alerts}
                    ''')
    with smtplib.SMTP_SSL(em.SMTP, em.Port) as server:
        server.login(em.Login,em.Password)
        server.send_message(msg)