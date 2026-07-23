import base64
import sys
from email.mime.text import MIMEText

import requests

from youtube_digest.main import load_config
from youtube_digest.youtube_client import refresh_access_token

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def send_email(access_token: str, to_address: str, from_address: str, subject: str, body_text: str) -> None:
    message = MIMEText(body_text, "plain", "utf-8")
    message["To"] = to_address
    message["From"] = from_address
    message["Subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")

    response = requests.post(
        GMAIL_SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw},
        timeout=15,
    )
    response.raise_for_status()


if __name__ == "__main__":
    config_path, subject, body_path = sys.argv[1], sys.argv[2], sys.argv[3]
    config = load_config(config_path)
    access_token = refresh_access_token(
        config["google_client_id"],
        config["google_client_secret"],
        config["google_refresh_token"],
    )
    with open(body_path, encoding="utf-8") as f:
        body_text = f.read()
    send_email(access_token, config["email_to"], config["email_from"], subject, body_text)
    print("sent")
