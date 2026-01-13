import json
import logging

from openai import OpenAI

from crimereporter.ai.ai_engine import AIEngine
from crimereporter.utils.config import Config

config = Config()
logger = logging.getLogger(__name__)


class OpenAIEngine(AIEngine):

    def __init__(self):
        cfg = self.load_config()
        with open(cfg.api_key_file) as f:
            openai_config = json.load(f)
        api_key = openai_config.get("api_key")
        if not api_key:
            raise ValueError("API key not found in the API key file")

        self.client = OpenAI(api_key=api_key)
        self.model = cfg.get("model")

    def generate(self, message: str) -> str:
        logger.info("Generating response using OpenAI")
        # noinspection PyTypeChecker
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message.content.strip()
