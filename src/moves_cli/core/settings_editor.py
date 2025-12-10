import copy
from importlib.resources import files
from typing import Any, Dict

import tomlkit

from moves_cli.models import Settings
from moves_cli.utils.data_handler import DataHandler


class SettingsEditor:
    template = files("moves_cli.data") / "settings_template.toml"

    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
        self.settings = self.data_handler.DATA_FOLDER / "settings.toml"

        self._template_doc = tomlkit.parse(self.template.read_text())
        self._template_defaults: Dict[str, Any] = dict(self._template_doc)

        try:
            user_data = dict(tomlkit.parse(self.data_handler.read(self.settings)))
        except Exception:
            user_data = {}

        self._data = {**self._template_defaults, **user_data}

        self._save()

    def _save(self) -> bool:
        try:
            self.settings.parent.mkdir(parents=True, exist_ok=True)
            node = copy.deepcopy(self._template_doc)

            for key in self._template_defaults.keys():
                if key in self._data:
                    node[key] = self._data[key]

            with self.settings.open("w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(node))
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to save settings: {e}") from e

    def set(self, key: str, value: Any) -> bool:
        if key not in self._template_defaults:
            return False

        self._data[key] = value
        try:
            self._save()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to set key '{key}': {e}") from e

    def unset(self, key: str) -> bool:
        if key in self._template_defaults:
            self._data[key] = self._template_defaults[key]
        else:
            self._data.pop(key, None)

        try:
            self._save()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to unset key '{key}': {e}") from e

    def list(self) -> Settings:
        return Settings(**self._data)
