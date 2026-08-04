import logging
from typing import Any

from discord.ext.commands import Cog

from ..utils import gen_config_hash


class BaseCog(Cog):
    """Base class for all cogs in the framework."""

    # If the config_key is not overridden to a non-None value,
    # then the cog will skip calling load_config at init
    # and will never be reloaded.
    config_key: str | None = None
    _config_hash: bytes

    def __init__(
        self, bot, config: dict[str, Any], logger_instance: logging.Logger
    ) -> None:
        """Initialize the cog with the bot, config data, and logger instance."""
        self.__bot = bot
        self.__logger = logger_instance

        try:
            if self.config_key is not None:
                self.load_config(config)
            self.log(f"Initialized {type(self).__name__}")
        except Exception as e:
            self.log(
                f"Failed to initialize {type(self).__name__}: {e}",
                level=logging.ERROR,
            )

    def log(
        self,
        message: str,
        level: int = logging.INFO,
    ) -> None:
        """Log a message using the logger instance with a specified level."""
        self.__logger.log(level, f"{type(self).__name__}:{message}")

    def __update(self, config: dict[str, Any]) -> None:
        """Update existing config data with new config data."""
        raise NotImplementedError(
            "Subclasses must override the 'update' method to load config data."
        )

    def load_config(self, config: dict[str, Any]) -> bool:
        """Load the config data and update if necessary."""
        try:
            config_hash = gen_config_hash(config)
            had_previous_config = self._config_hash is not None

            if config_hash != self._config_hash:
                self.__update(config)
                self._config_hash = config_hash
                # This if avoids logging during init, when there is
                # other init-specific logging happening.
                if had_previous_config:
                    self.log(f"Updated {type(self).__name__} config")
                return True
            return False
        except Exception as e:
            self.log(
                f"Failed to load config for {type(self).__name__}: {e}",
                level=logging.ERROR,
            )
            return False
