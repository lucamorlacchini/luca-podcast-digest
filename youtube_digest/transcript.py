import requests

TRANSCRIPT_API_URL = "https://transcriptapi.com/api/v2/youtube/transcript"


def fetch_transcript(video_id: str, api_key: str) -> str | None:
    try:
        response = requests.get(
            TRANSCRIPT_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"video_url": video_id},
            timeout=30,
        )
        response.raise_for_status()
        segments = response.json().get("transcript", [])
        text = " ".join(segment["text"] for segment in segments)
        return text or None
    except Exception:
        return None
