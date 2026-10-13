import requests

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]
