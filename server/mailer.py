import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic_settings import BaseSettings


class MailSettings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email: str


mail_settings = MailSettings(_env_file='./mailer.env', _env_file_encoding='utf-8')


def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = mail_settings.email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP_SSL(mail_settings.smtp_host, mail_settings.smtp_port) as server:
        server.login(mail_settings.smtp_user, mail_settings.smtp_password)
        server.send_message(msg)


class EmailNotifier:
    def __init__(self, default_to: str | None = None):
        self.default_to = default_to

    def __call__(self, to_email: str | None = None, subject: str = "Уведомление", body: str = ""):
        if not to_email:
            if not self.default_to:
                raise ValueError("Адрес получателя не указан")
            to_email = self.default_to

        send_email(to_email, subject, body)