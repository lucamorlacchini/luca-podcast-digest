from youtube_transcript_api import YouTubeTranscriptApi


def fetch_transcript(video_id: str) -> str | None:
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(segment["text"] for segment in segments)
    except Exception:
        return None
