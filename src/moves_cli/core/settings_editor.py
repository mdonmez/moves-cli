from typing import Any

import tomlkit

from moves_cli.config import DEFAULT_API_KEY, DEFAULT_LLM_MODEL
from moves_cli.models import Settings
from moves_cli.utils.data_handler import DataHandler


class SettingsEditor:
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
        self.settings = self.data_handler.DATA_FOLDER / "settings.toml"

        self._template_defaults: dict[str, Any] = {
            "model": DEFAULT_LLM_MODEL,
            "key": DEFAULT_API_KEY,
        }

        try:
            user_data = dict(tomlkit.parse(self.data_handler.read(self.settings)))
        except Exception:
            user_data = {}

        self._data = {**self._template_defaults, **user_data}

        self._save()

    def _save(self) -> bool:
        try:
            self.settings.parent.mkdir(parents=True, exist_ok=True)

            doc = tomlkit.document()

            doc.add(tomlkit.comment("moves CLI Configuration"))

            doc.add(tomlkit.nl())

            for key in self._template_defaults.keys():
                if key == "model":
                    doc.add(
                        tomlkit.comment(
                            "LLM model for speaker processing, find models at: https://models.litellm.ai/"
                        )
                    )
                elif key == "key":
                    doc.add(tomlkit.comment("API key for the LLM provider"))

                value = self._data.get(key)
                doc[key] = value if value is not None else ""

            with self.settings.open("w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(doc))
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
        return Settings(
            model=self._data.get("model") or None,
            key=self._data.get("key") or None,
        )
