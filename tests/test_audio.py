import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from telegram_llm_bot.shared import audio


class Segment:
    text = " hello "


class AudioTranscriptionTest(unittest.IsolatedAsyncioTestCase):
    async def test_transcribes_with_local_model_and_removes_temp_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "voice.oga"
            model = Mock()
            model.transcribe.return_value = ([Segment()], None)

            with patch("telegram_llm_bot.shared.audio.temp_audio_path", return_value=path):
                with patch(
                    "telegram_llm_bot.shared.audio.local_transcription_model", return_value=model
                ):
                    text = await audio.transcribe(b"voice-bytes")

        self.assertEqual(text, "hello")
        self.assertFalse(path.exists())

    def test_local_transcription_defaults_fit_low_ram_cpu(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(audio.transcription_model(), "small")
            self.assertEqual(audio.transcription_compute_type(), "int8")
            self.assertEqual(audio.transcription_device(), "cpu")


if __name__ == "__main__":
    unittest.main()
