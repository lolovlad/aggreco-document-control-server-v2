from jinja2 import Environment, FileSystemLoader, select_autoescape
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic_settings import BaseSettings
from pathlib import Path
from .settings import settings


class MailSettings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email: str


mail_settings = MailSettings(_env_file='./mailer.env', _env_file_encoding='utf-8')

TEMPLATES_DIR = Path(Path(settings.root_path).parent, "templates", "emails")
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"])
)


def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    msg = MIMEMultipart()
    msg["From"] = mail_settings.email
    msg["To"] = to_email
    msg["Subject"] = subject

    mime_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, mime_type, "utf-8"))

    with smtplib.SMTP_SSL(mail_settings.smtp_host, mail_settings.smtp_port) as server:
        server.login(mail_settings.smtp_user, mail_settings.smtp_password)
        server.send_message(msg)


class EmailNotifier:
    def __init__(self, default_to: str | None = None):
        self.default_to = default_to

    def __call__(self,
                 to_email: str | None = None,
                 subject: str = "Уведомление",
                 template_name: str | None = None,
                 context: dict | None = None,
                 is_html: bool = True):
        if not to_email:
            if not self.default_to:
                raise ValueError("Адрес получателя не указан")
            to_email = self.default_to

        if template_name:
            context = context or {}
            template = env.get_template(template_name)
            body = template.render(**context)
        else:
            body = context.get("body", "") if context else ""

        send_email(to_email, subject, body, is_html=is_html)