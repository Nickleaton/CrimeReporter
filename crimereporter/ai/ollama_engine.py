import logging
import re

import ollama

from crimereporter.ai.ai_engine import AIEngine
from crimereporter.utils.config import Config

config = Config()
logger = logging.getLogger(__name__)


class OllamaEngine(AIEngine):
    """AI engine implementation using Ollama."""

    def generate(self, message: str) -> str:
        """
        Generate a response from Ollama based on the input message.

        Args:
            message: The input message to send to the AI.

        Returns:
            The AI-generated response as a string.
        """
        logger.info("Generating response using Ollama")
        cfg = self.load_config()
        try:
            response = ollama.chat(
                model=cfg.model,
                messages=[{"role": "user", "content": message}],
            )
            content = response["message"]["content"].strip()
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return content
        except Exception as e:
            logger.error("Ollama generation failed: %s", e)
            raise
