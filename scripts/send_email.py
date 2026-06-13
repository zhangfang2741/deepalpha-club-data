from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"缺少邮件配置：{name}")
    return value


def _parse_recipients(value: str) -> list[str]:
    recipients = [email.strip() for email in value.split(",") if email.strip()]
    if not recipients:
        raise RuntimeError("缺少邮件配置：EMAIL_TO")
    return recipients


def send_email(subject: str, body: str, html_body: str | None = None) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = _required_env("SMTP_USER")
    password = _required_env("SMTP_PASS")
    recipients = _parse_recipients(_required_env("EMAIL_TO"))

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = username
    message["To"] = ", ".join(recipients)
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message, from_addr=username, to_addrs=recipients)


def main() -> None:
    parser = argparse.ArgumentParser(description="发送纯文本邮件")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--html-body-file")
    args = parser.parse_args()

    load_dotenv()
    body = Path(args.body_file).read_text(encoding="utf-8")
    html_body = (
        Path(args.html_body_file).read_text(encoding="utf-8") if args.html_body_file else None
    )
    send_email(args.subject, body, html_body=html_body)


if __name__ == "__main__":
    main()
