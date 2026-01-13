import inspect
from abc import ABC, ABCMeta, abstractmethod
from typing import Type

from moviepy.Clip import Clip


class SegmentMeta(ABCMeta):
    """Metaclass that registers all concrete Segment subclasses."""

    registry: dict[str, Type["Segment"]] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip registration for abstract base classes
        if not inspect.isabstract(cls) and issubclass(cls, Segment):
            segment_name = getattr(cls, "name", cls.__name__)
            SegmentMeta.registry[segment_name] = cls

        return cls


class Segment(ABC, metaclass=SegmentMeta):
    name: str = "segment"

    def __init__(self, idx, segment, fmt, output_path, default_text):
        self.idx = idx
        self.segment = segment
        self.fmt = fmt
        self.output_path = output_path
        self.default_text = default_text

    @abstractmethod
    def load(self) -> Clip:
        """Return a MoviePy clip"""
        raise NotImplementedError
