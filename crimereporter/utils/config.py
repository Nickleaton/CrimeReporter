import os
from collections.abc import Mapping
from pathlib import Path

import yaml


class ConfigNamespace(Mapping):
    """Nested dictionary wrapper supporting attribute-style access."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        value = self._data[key]
        if isinstance(value, dict):
            return ConfigNamespace(value)
        return value

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __getattr__(self, name):
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return ConfigNamespace(value)
            return value
        raise AttributeError(f"'ConfigNamespace' object has no attribute '{name}'")

    def to_dict(self) -> dict:
        """Convert to a plain dictionary recursively."""
        result = {}
        for k, v in self._data.items():
            if isinstance(v, dict):
                result[k] = ConfigNamespace(v).to_dict()
            else:
                result[k] = v
        return result

    def items(self):
        return self._data.items()

    def __repr__(self):
        return f"ConfigNamespace(keys={list(self._data.keys())})"


class ConfigBase(Mapping):
    """Base configuration class with YAML loading and dict/attribute access."""

    def __init__(self, path: str):
        self.path = Path(path)
        self._data = {}
        self.load()

    def load(self) -> None:
        """Load YAML configuration from file."""
        if not self.path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.path}")
        with self.path.open(encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

    def reload(self) -> None:
        """Reload configuration from the original path."""
        self.load()

    # Mapping interface
    def __getitem__(self, key):
        value = self._data[key]
        if isinstance(value, dict):
            return ConfigNamespace(value)
        return value

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    # Attribute-style access
    def __getattr__(self, name):
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return ConfigNamespace(value)
            return value
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def to_dict(self) -> dict:
        """Convert configuration to a plain dictionary recursively."""
        result = {}
        for k, v in self._data.items():
            if isinstance(v, dict):
                result[k] = ConfigNamespace(v).to_dict()
            else:
                result[k] = v
        return result

    def __repr__(self):
        return f"{type(self).__name__}(path={self.path}, keys={list(self._data.keys())})"


class Config(ConfigBase):
    """Singleton global configuration loader."""

    _instance = None

    def __new__(cls, path: str = "configuration/config.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, path: str = "configuration/config.yaml"):
        if self.__initialized:
            return

        super().__init__(path)

        # ---- data root from global env var ----
        try:
            self.data_root = Path(os.environ["CRIMEREPORTER"])
        except KeyError:
            raise RuntimeError("CRIMEREPORTER environment variable is not set")

        self.__initialized = True

class FormatsConfig(ConfigBase):
    """Configuration for formats, sharing the same base logic."""

    def __init__(self, orientation: str, category: str):
        super().__init__(f"configuration/{orientation}_{category}.yaml")
