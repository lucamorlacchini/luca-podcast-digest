import base64
import email
from unittest.mock import patch, MagicMock

from youtube_digest.send_email import send_email


def test_send_email_posts_correct_gmail_payload():
    response = MagicMock()
    response.raise_for_status.return_value = None

    with patch("youtube_digest.send_email.requests.post", return_value=response) as mock_post:
        send_email(
            access_token="fake-token",
            to_address="luca@alesea.com",
            from_address="luca.morlacchini@gmail.com",
            subject="Test Subject",
            body_text="Ciao mondo",
        )

    assert mock_post.call_count == 1
    args, kwargs = mock_post.call_args
    assert args[0] == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    assert kwargs["headers"] == {"Authorization": "Bearer fake-token"}

    raw = kwargs["json"]["raw"]
    raw_bytes = base64.urlsafe_b64decode(raw.encode("ascii"))
    parsed = email.message_from_bytes(raw_bytes)
    assert parsed["Subject"] == "Test Subject"
    assert parsed["To"] == "luca@alesea.com"
    assert parsed["From"] == "luca.morlacchini@gmail.com"
    assert parsed.get_payload(decode=True).decode("utf-8") == "Ciao mondo"


def test_send_email_raises_on_http_error():
    response = MagicMock()
    response.raise_for_status.side_effect = Exception("500 server error")

    with patch("youtube_digest.send_email.requests.post", return_value=response):
        try:
            send_email(
                access_token="fake-token",
                to_address="luca@alesea.com",
                from_address="luca.morlacchini@gmail.com",
                subject="Test Subject",
                body_text="Ciao mondo",
            )
            assert False, "expected an exception to propagate"
        except Exception as exc:
            assert "500 server error" in str(exc)
