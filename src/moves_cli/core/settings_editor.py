from typing import Any

import keyring
import tomlkit

from moves_cli.config import DEFAULT_LLM_MODEL
from moves_cli.models import Settings
from moves_cli.utils.data_handler import DataHandler

# Keyring service and username constants
KEYRING_SERVICE = "moves-cli"
KEYRING_USERNAME = "api-key"


class SettingsEditor:
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
        self.settings = self.data_handler.DATA_FOLDER / "settings.toml"

        self._template_defaults: dict[str, Any] = {
            "model": DEFAULT_LLM_MODEL,
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
            doc.add(
                tomlkit.comment("Note: API key is stored securely in system keyring")
            )

            doc.add(tomlkit.nl())

            for key in self._template_defaults.keys():
                match key:
                    case "model":
                        doc.add(
                            tomlkit.comment(
                                "LLM model for speaker processing, find models at: https://models.litellm.ai/"
                            )
                        )

                value = self._data.get(key)
                doc[key] = value if value is not None else ""

            with self.settings.open("w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(doc))
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to save settings: {e}") from e

    def set(self, key: str, value: Any) -> bool:
        if key == "key":
            # Store API key in keyring
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, value)
                return True
            except keyring.errors.PasswordSetError as e:
                raise RuntimeError(f"Failed to store API key in keyring: {e}") from e
        elif key in self._template_defaults:
            # Store other settings in toml file
            self._data[key] = value
            try:
                self._save()
                return True
            except Exception as e:
                raise RuntimeError(f"Failed to set key '{key}': {e}") from e
        else:
            return False

    def unset(self, key: str) -> bool:
        if key == "key":
            # Delete API key from keyring
            try:
                keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
                return True
            except keyring.errors.PasswordDeleteError:
                # Key doesn't exist, that's fine
                return True
            except Exception as e:
                raise RuntimeError(f"Failed to delete API key from keyring: {e}") from e
        elif key in self._template_defaults:
            # Reset other settings to default
            self._data[key] = self._template_defaults[key]
            try:
                self._save()
                return True
            except Exception as e:
                raise RuntimeError(f"Failed to unset key '{key}': {e}") from e
        else:
            self._data.pop(key, None)
            try:
                self._save()
                return True
            except Exception as e:
                raise RuntimeError(f"Failed to unset key '{key}': {e}") from e

    def list(self) -> Settings:
        # Get API key from keyring
        api_key = None
        try:
            api_key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception:
            # Keyring access failed, key doesn't exist
            pass

        return Settings(
            model=self._data.get("model") or None,
            key=api_key,
        )
