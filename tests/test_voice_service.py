import os
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from telegram_llm_bot.bots.base_chatbot.services import voice


class VoiceServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_storage_failure_does_not_block_transcription(self):
        with patch.dict(
            os.environ,
            {
                "BOT_NAME": "bot",
                "MINIO_ENDPOINT_URL": "http://user:secret@localhost:9000",
                "MINIO_BUCKET": "bucket",
            },
            clear=False,
        ):
            with patch(
                "telegram_llm_bot.bots.base_chatbot.services.voice.get_active_session",
                new=AsyncMock(return_value="default"),
            ):
                with patch.object(
                    voice.minio_storage,
                    "put_object",
                    new=AsyncMock(side_effect=RuntimeError("storage down")),
                ):
                    with patch(
                        "telegram_llm_bot.bots.base_chatbot.services.voice.transcribe",
                        new=AsyncMock(return_value="hello"),
                    ) as transcribe:
                        with patch(
                            "telegram_llm_bot.bots.base_chatbot.services.voice.text_chat_service",
                            new=AsyncMock(return_value="reply"),
                        ) as text_chat:
                            with self.assertLogs(
                                "telegram_llm_bot.bots.base_chatbot.services.voice",
                                level="WARNING",
                            ) as logs:
                                reply = await voice.voice_chat_service(
                                    b"voice",
                                    user_id=1,
                                    duration=2,
                                    msg_date=datetime(2026, 1, 1),
                                )

        self.assertEqual(reply, "reply")
        transcribe.assert_awaited_once()
        text_chat.assert_awaited_once()
        log_text = "\n".join(logs.output)
        self.assertIn("Voice archive storage failed", log_text)
        self.assertIn("bucket=bucket", log_text)
        self.assertIn("object=voice/1/default/", log_text)
        self.assertIn("endpoint=http://localhost:9000", log_text)
        self.assertNotIn("secret", log_text)

    def test_sanitized_endpoint_strips_credentials(self):
        self.assertEqual(
            voice.sanitized_endpoint("http://user:secret@localhost:9000/path"),
            "http://localhost:9000",
        )


if __name__ == "__main__":
    unittest.main()
