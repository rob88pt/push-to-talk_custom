import os
from loguru import logger
import time
from typing import Optional
from openai import OpenAI, APIError as OpenAIAPIError

from src.transcription_base import TranscriberBase
from src.utils import validate_audio_file_exists, validate_audio_duration
from src.exceptions import TranscriptionError, APIError

_MAX_RETRIES = 5
_RETRY_DELAY = 3  # seconds


class OpenAITranscriber(TranscriberBase):
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        Initialize the transcriber with OpenAI API.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: STT Model to use (default: whisper-1)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(api_key, "OpenAI")

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text using OpenAI API.

        Args:
            audio_file_path: Path to the audio file
            language: Language code (optional, auto-detect if None)

        Returns:
            Transcribed text or None if transcription failed
        """
        # Validate file exists
        if not validate_audio_file_exists(audio_file_path):
            return None

        # Validate audio duration
        if not validate_audio_duration(audio_file_path):
            return None

        start_time = time.time()
        logger.debug(f"Starting transcription for: {audio_file_path}")
        prompt = ", ".join(self.glossary) if self.glossary else None

        last_error: Exception = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Calling OpenAI transcription API (model: {self.model}, language: {language})"
                    + (f", attempt {attempt}/{_MAX_RETRIES}" if attempt > 1 else "")
                )

                with open(audio_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language,
                        prompt=prompt,
                        response_format="text",
                    )

                if not response or not str(response).strip():
                    logger.error("OpenAI transcription API returned empty response")
                    return None

                logger.debug(f"OpenAI transcription response: {response}")

                if hasattr(response, "text"):
                    transcribed_text = response.text
                elif isinstance(response, str):
                    transcribed_text = response
                else:
                    logger.warning(
                        "Unknown transcription response format, using string representation"
                    )
                    transcribed_text = str(response)

                transcribed_text = transcribed_text.strip()
                transcription_time = time.time() - start_time
                logger.info(
                    f"Transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
                )
                return transcribed_text if transcribed_text else None

            except OpenAIAPIError as e:
                last_error = APIError(
                    f"OpenAI transcription API failed: {e}",
                    provider="OpenAI",
                    status_code=getattr(e, "status_code", None),
                )
                # Don't retry on auth/client errors (4xx), only on connection/server errors
                status = getattr(e, "status_code", None)
                if status is not None and 400 <= status < 500:
                    logger.error(f"OpenAI API client error (not retrying): {e}")
                    raise last_error from e
                logger.warning(f"OpenAI API error (attempt {attempt}/{_MAX_RETRIES}): {e}")
            except Exception as e:
                last_error = TranscriptionError(f"Failed to transcribe audio: {e}")
                logger.warning(f"Transcription error (attempt {attempt}/{_MAX_RETRIES}): {e}")

            if attempt < _MAX_RETRIES:
                logger.info(f"Retrying in {_RETRY_DELAY}s...")
                time.sleep(_RETRY_DELAY)

        logger.error(f"Transcription failed after {_MAX_RETRIES} attempts")
        raise last_error
