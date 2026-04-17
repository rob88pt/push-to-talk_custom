import pytest
import os
from unittest.mock import MagicMock
from loguru import logger

from src.transcription_groq import GroqTranscriber
from src.exceptions import ConfigurationError, TranscriptionError, APIError


class TestGroqTranscriber:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        mocker.patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"})
        # Patch groq.Groq so no real client is created
        self.mock_groq_class = mocker.patch("src.transcription_groq.groq.Groq")
        self.mock_client = MagicMock()
        self.mock_groq_class.return_value = self.mock_client
        self.transcriber = GroqTranscriber()

    def test_initialization_with_env_var(self, mocker):
        mocker.patch.dict(os.environ, {"GROQ_API_KEY": "env-groq-key"})
        mock_class = mocker.patch("src.transcription_groq.groq.Groq")
        t = GroqTranscriber()
        assert t.api_key == "env-groq-key"
        assert t.model == "whisper-large-v3-turbo"
        mock_class.assert_called_once_with(api_key="env-groq-key")

    def test_initialization_with_explicit_key(self, mocker):
        mock_class = mocker.patch("src.transcription_groq.groq.Groq")
        t = GroqTranscriber(api_key="explicit-key", model="whisper-large-v3")
        assert t.api_key == "explicit-key"
        assert t.model == "whisper-large-v3"

    def test_initialization_no_api_key(self, mocker):
        mocker.patch.dict(os.environ, {}, clear=True)
        mocker.patch("src.transcription_groq.groq.Groq")
        with pytest.raises(ConfigurationError, match="Groq API key is required"):
            GroqTranscriber()

    def test_transcribe_audio_success(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "Hello world"
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav")
        assert result == "Hello world"
        self.mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = self.mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["model"] == "whisper-large-v3-turbo"

    def test_transcribe_audio_with_language(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "Bonjour"
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav", language="fr")
        assert result == "Bonjour"
        call_kwargs = self.mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["language"] == "fr"

    def test_transcribe_audio_file_not_found(self, mocker):
        mocker.patch("os.path.exists", return_value=False)
        result = self.transcriber.transcribe_audio("nonexistent.wav")
        assert result is None
        self.mock_client.audio.transcriptions.create.assert_not_called()

    def test_transcribe_audio_empty_response(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = ""
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav")
        assert result is None

    def test_transcribe_audio_whitespace_response(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "   \n  "
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav")
        assert result is None

    def test_retry_on_transient_error_then_success(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("time.sleep")  # don't actually wait 3s in tests

        transient_error = Exception("Connection reset")
        mock_response = MagicMock()
        mock_response.text = "Retry succeeded"
        self.mock_client.audio.transcriptions.create.side_effect = [
            transient_error,
            mock_response,
        ]

        result = self.transcriber.transcribe_audio("test.wav")
        assert result == "Retry succeeded"
        assert self.mock_client.audio.transcriptions.create.call_count == 2

    def test_no_retry_on_4xx_error(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("time.sleep")

        import groq as groq_module
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        err = groq_module.APIStatusError(
            "Unauthorized",
            response=mock_resp,
            body=None,
        )
        self.mock_client.audio.transcriptions.create.side_effect = err

        with pytest.raises(APIError):
            self.transcriber.transcribe_audio("test.wav")
        assert self.mock_client.audio.transcriptions.create.call_count == 1

    def test_raises_after_all_retries_exhausted(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("time.sleep")

        self.mock_client.audio.transcriptions.create.side_effect = Exception("Network down")

        with pytest.raises(TranscriptionError):
            self.transcriber.transcribe_audio("test.wav")
        assert self.mock_client.audio.transcriptions.create.call_count == 5

    def test_glossary_passed_as_prompt(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "Result"
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        self.transcriber.set_glossary(["foo", "bar"])
        self.transcriber.transcribe_audio("test.wav")

        call_kwargs = self.mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["prompt"] == "foo, bar"
