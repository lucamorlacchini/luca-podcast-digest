import requests

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


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


def get_subscribed_channels(access_token: str) -> list[dict]:
    channels = []
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"part": "snippet", "mine": "true", "maxResults": 50}
    url = f"{YOUTUBE_API_BASE}/subscriptions"
    while True:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        for item in data["items"]:
            channels.append({
                "channel_id": item["snippet"]["resourceId"]["channelId"],
                "title": item["snippet"]["title"],
            })
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        params["pageToken"] = next_token
    return channels


def get_uploads_playlist_id(access_token: str, channel_id: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"part": "contentDetails", "id": channel_id}
    response = requests.get(f"{YOUTUBE_API_BASE}/channels", headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_todays_videos(access_token: str, uploads_playlist_id: str, today_iso_date: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"part": "snippet", "playlistId": uploads_playlist_id, "maxResults": 10}
    response = requests.get(f"{YOUTUBE_API_BASE}/playlistItems", headers=headers, params=params, timeout=10)
    response.raise_for_status()
    videos = []
    for item in response.json()["items"]:
        snippet = item["snippet"]
        if not snippet["publishedAt"].startswith(today_iso_date):
            continue
        videos.append({
            "video_id": snippet["resourceId"]["videoId"],
            "title": snippet["title"],
            "published_at": snippet["publishedAt"],
            "description": snippet.get("description", ""),
        })
    return videos
