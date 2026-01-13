from abc import ABC, abstractmethod

from crimereporter.utils.config import Config, ConfigNamespace

config = Config()


class AIEngine(ABC):

    registry: dict[str, type["AIEngine"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Only register concrete classes (no abstract methods)
        if getattr(cls, "__abstractmethods__", None):
            return
        name = cls.__name__.removesuffix("Engine")
        if name in cls.registry:
            return
        cls.registry[name] = cls

    @property
    def name(self) -> str:
        return self.__class__.__name__.removesuffix("Engine")

    @abstractmethod
    def generate(self, message: str) -> str:
        """Generate a response based on the input message."""
        pass

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> "AIEngine":
        """Create an AIEngine instance by registered name."""
        engine_cls = cls.registry.get(name)
        if engine_cls is None:
            raise ValueError(f"Unknown AI engine: {name}. Registered engines: {list(cls.registry.keys())}")
        return engine_cls(*args, **kwargs)

    from crimereporter.utils.config import ConfigNamespace

    @classmethod
    def load_config(cls) -> ConfigNamespace:
        """
        Load this engine's configuration from config.engines based on its class name.
        Returns a ConfigNamespace for easy attribute-style access.
        """
        engine_name = cls.__name__.removesuffix("Engine").lower()

        for engine_entry in config.engines:
            engine_cfg = engine_entry.get("engine")
            if engine_cfg and engine_cfg.get("name", "").lower() == engine_name:
                return ConfigNamespace(engine_cfg)

        raise ValueError(f"No configuration found for {engine_name} in config.engines")
