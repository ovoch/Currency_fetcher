import smtplib
import logging
from email.message import EmailMessage
from core.email_config import em

logger = logging.getLogger(__name__)


def send_email_with_alerts(email:str, alerts: list):
    if not alerts:
        logger.warning("Alerts is None")
        return  
    msg = EmailMessage()
    msg['From'] = em.Login
    msg['To'] = email
    msg['Subject'] = "Rate alert"
    alert_lines = [f"{alert["base"]}:{alert["target"]} -> Rates: target:{alert["rate"]}, current:{alert["current_rate"]}" for alert in alerts]
    message = "\n".join(alert_lines)
    msg.set_content(message)
    with smtplib.SMTP(timeout=10) as server:
        server.set_debuglevel(1)              
        try:
            server.connect(em.SMTP, em.Port)
            if server.has_extn("STARTTLS"):
                server.starttls()
            if em.Password and server.has_extn("AUTH"):
                server.login(em.Login, em.Password) 
            server.send_message(msg)
            logger.info(f"{email} send {len(alerts)} alerts")
        except (smtplib.SMTPException, OSError):
            logger.exception("The connection is failed")
            raise
        
    
    