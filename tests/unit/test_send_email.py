import smtplib

import pytest

from scripts import send_email


class FakeSMTP:
    instances = []

    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args = None
        self.sent_messages = []
        self.sendmail_args = None
        FakeSMTP.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.login_args = (username, password)

    def send_message(self, message, from_addr=None, to_addrs=None) -> None:  # type: ignore[no-untyped-def]
        self.sendmail_args = (from_addr or message["From"], to_addrs or message["To"])
        self.sent_messages.append(message)


def test_send_email_uses_smtp_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSMTP.instances = []
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("EMAIL_TO", "receiver@example.com")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    send_email.send_email("标题", "正文内容")

    smtp = FakeSMTP.instances[0]
    assert smtp.host == "smtp.gmail.com"
    assert smtp.port == 587
    assert smtp.started_tls is True
    assert smtp.login_args == ("sender@example.com", "app-password")
    message = smtp.sent_messages[0]
    assert message["Subject"] == "标题"
    assert message["From"] == "sender@example.com"
    assert message["To"] == "receiver@example.com"
    assert message.get_content().strip() == "正文内容"


def test_send_email_can_send_html_with_text_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSMTP.instances = []
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("EMAIL_TO", "receiver@example.com")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    send_email.send_email("标题", "纯文本正文", html_body="<h1>HTML 正文</h1>")

    message = FakeSMTP.instances[0].sent_messages[0]
    assert message.is_multipart()
    plain_part, html_part = message.get_payload()
    assert plain_part.get_content_type() == "text/plain"
    assert plain_part.get_content().strip() == "纯文本正文"
    assert html_part.get_content_type() == "text/html"
    assert "<h1>HTML 正文</h1>" in html_part.get_content()


def test_send_email_supports_multiple_recipients(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSMTP.instances = []
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("EMAIL_TO", "first@example.com, second@example.com")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    send_email.send_email("标题", "正文内容")

    message = FakeSMTP.instances[0].sent_messages[0]
    assert message["To"] == "first@example.com, second@example.com"
    assert FakeSMTP.instances[0].sendmail_args == (
        "sender@example.com",
        ["first@example.com", "second@example.com"],
    )


def test_send_email_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    monkeypatch.delenv("EMAIL_TO", raising=False)

    with pytest.raises(RuntimeError, match="缺少邮件配置"):
        send_email.send_email("标题", "正文内容")
