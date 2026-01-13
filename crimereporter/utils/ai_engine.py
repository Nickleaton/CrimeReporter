from abc import ABC, abstractmethod
from typing import List

from gpt4all import GPT4All
from openai import OpenAI


class AIEngine(ABC):
    """Abstract interface for an AI engine."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from the given prompt."""
        pass

    @abstractmethod
    def generate_chat(self, messages: List[dict[str, str]]) -> str:
        """Generate text from chat-style messages."""
        pass


class OpenAIEngine(AIEngine):
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def generate_chat(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content.strip()


class LocalLLMEngine(AIEngine):
    def __init__(self, model_path: str):
        self.model = GPT4All(model_path)

    def generate(self, prompt: str) -> str:
        return self.model.generate(prompt)

    def generate_chat(self, messages: list[dict[str, str]]) -> str:
        # GPT4All does not natively support chat format; flatten messages
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        return self.model.generate(prompt)
