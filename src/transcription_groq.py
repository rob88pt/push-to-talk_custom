import os
from loguru import logger
import time
from typing import Optional
import groq

from src.transcription_base import TranscriberBase
from src.utils import validate_audio_file_exists, validate_audio_duration
from src.exceptions import TranscriptionError, APIError

_MAX_RETRIES = 5
_RETRY_DELAY = 3  # seconds


class GroqTranscriber(TranscriberBase):
    """Transcriber implementation using the Groq API (Whisper models)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-large-v3-turbo"):
        """
        Initialize the transcriber with Groq API.

        Args:
            api_key: Groq API key. If None, will use GROQ_API_KEY environment variable
            model: STT Model to use (default: whisper-large-v3-turbo)
        """
        api_key = api_key or os.getenv("GROQ_API_KEY")
        super().__init__(api_key, "Groq")
        self.model = model
        self.client = groq.Groq(api_key=self.api_key)

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text using Groq API.

        Args:
            audio_file_path: Path to the audio file
            language: Language code (optional, auto-detect if None)

        Returns:
            Transcribed text or None if transcription failed
        """
        if not validate_audio_file_exists(audio_file_path):
            return None
        if not validate_audio_duration(audio_file_path):
            return None

        start_time = time.time()
        logger.debug(f"Starting transcription for: {audio_file_path}")
        prompt = ", ".join(self.glossary) if self.glossary else None

        last_error: Exception = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Calling Groq transcription API (model: {self.model}, language: {language})"
                    + (f", attempt {attempt}/{_MAX_RETRIES}" if attempt > 1 else "")
                )
                with open(audio_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language,
                        prompt=prompt,
                    )

                if not response:
                    logger.error("Groq transcription API returned empty response")
                    return None

                if hasattr(response, "text"):
                    transcribed_text = response.text
                elif isinstance(response, str):
                    transcribed_text = response
                else:
                    logger.warning("Unknown transcription response format, using string representation")
                    transcribed_text = str(response)

                if not transcribed_text or not transcribed_text.strip():
                    logger.error("Groq transcription API returned empty response")
                    return None

                transcribed_text = transcribed_text.strip()
                transcription_time = time.time() - start_time
                logger.info(
                    f"Transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
                )
                return transcribed_text

            except groq.APIStatusError as e:
                last_error = APIError(
                    f"Groq transcription API failed: {e}",
                    provider="Groq",
                    status_code=e.status_code,
                )
                if 400 <= e.status_code < 500:
                    logger.error(f"Groq API client error (not retrying): {e}")
                    raise last_error from e
                logger.warning(f"Groq API error (attempt {attempt}/{_MAX_RETRIES}): {e}")
            except Exception as e:
                last_error = TranscriptionError(f"Failed to transcribe audio: {e}")
                logger.warning(f"Transcription error (attempt {attempt}/{_MAX_RETRIES}): {e}")

            if attempt < _MAX_RETRIES:
                logger.info(f"Retrying in {_RETRY_DELAY}s...")
                time.sleep(_RETRY_DELAY)

        logger.error(f"Transcription failed after {_MAX_RETRIES} attempts")
        raise last_error
