# mailer.py
import os
import smtplib
import mimetypes
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

def _as_list(s: str | None):
    if not s: return []
    return [addr.strip() for addr in s.split(",") if addr.strip()]

def send_mail(subject: str, body_text: str, attachments: list[str] | None = None):
    user = os.environ["GMAIL_USER"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_list = _as_list(os.environ.get("GMAIL_TO"))

    if not to_list:
        raise RuntimeError("GMAIL_TO is empty")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(to_list)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-Id"] = make_msgid()

    # シンプルなプレーンテキスト本文（必要ならHTMLを追加してもOK）
    msg.set_content(body_text)

    # 添付
    for path in (attachments or []):
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(user, app_password)
        s.send_message(msg)
