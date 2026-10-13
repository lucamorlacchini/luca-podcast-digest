import os
import subprocess
import tempfile
import time

import imageio_ffmpeg
import requests

from podcast_digest.feeds import HEADERS

GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"
GROQ_MAX_BYTES = 25 * 1024 * 1024
# How long to wait out a Groq rate limit before giving up on that episode.
MAX_RATE_LIMIT_WAIT_S = 120


class TranscriptionError(Exception):
    """Raised with a short Italian reason that ends up in the email next to the episode."""


def download_audio(audio_url: str, dest_path: str) -> None:
    with requests.get(audio_url, headers=HEADERS, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)


def compress_audio(src_path: str, dest_path: str) -> None:
    # Mono 16 kHz Opus at 16 kbit/s: ~7 MB per hour, so episodes up to ~3.5 h
    # fit Groq's 25 MB upload limit, and speech recognition quality is unaffected.
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
         "-i", src_path, "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "libopus", "-b:a", "16k", "-application", "voip", dest_path],
        check=True,
    )


def transcribe_file(path: str, api_key: str) -> str:
    for attempt in range(3):
        with open(path, "rb") as f:
            response = requests.post(
                GROQ_TRANSCRIBE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                data={"model": GROQ_MODEL, "response_format": "text"},
                files={"file": (os.path.basename(path), f, "audio/ogg")},
                timeout=600,
            )
        if response.status_code == 429:
            wait = float(response.headers.get("retry-after", 60))
            if wait > MAX_RATE_LIMIT_WAIT_S or attempt == 2:
                raise TranscriptionError("limite giornaliero/orario di Groq raggiunto")
            time.sleep(wait)
            continue
        if response.status_code == 401:
            raise TranscriptionError("chiave Groq non valida o scaduta")
        response.raise_for_status()
        return response.text.strip()
    raise TranscriptionError("limite di Groq raggiunto")


def transcribe_episode(audio_url: str, api_key: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        original = os.path.join(tmp, "episode_audio")
        compressed = os.path.join(tmp, "episode.ogg")
        try:
            download_audio(audio_url, original)
        except requests.RequestException as exc:
            raise TranscriptionError(f"download dell'audio non riuscito ({type(exc).__name__})") from exc
        try:
            compress_audio(original, compressed)
        except subprocess.CalledProcessError as exc:
            raise TranscriptionError("conversione dell'audio non riuscita") from exc
        if os.path.getsize(compressed) > GROQ_MAX_BYTES:
            raise TranscriptionError("episodio troppo lungo per la trascrizione (oltre ~3,5 ore)")
        try:
            text = transcribe_file(compressed, api_key)
        except requests.RequestException as exc:
            raise TranscriptionError(f"errore del servizio di trascrizione ({type(exc).__name__})") from exc
        if not text:
            raise TranscriptionError("trascrizione vuota")
        return text
