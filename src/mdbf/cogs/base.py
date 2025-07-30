from os import environ
import logging

from discord.ext.commands import Cog

from ..utils import gen_config_hash


class BaseCog(Cog, guild_ids=[int(environ.get("BOT_GUILD_ID", 0))]):
    """Base class for all cogs in the framework."""

    config_hash: bytes
    cogname: str

    LOG_LEVELS = {
        "debug": logging.debug,
        "info": logging.info,
        "warning": logging.warning,
        "error": logging.error,
        "critical": logging.critical,
    }

    def __init__(self, bot, config: dict, logger_instance: logging.Logger) -> None:
        """Initialize the cog with the bot, config data, and logger instance."""
        self.bot = bot
        self.logger = logger_instance

        try:
            self.load_config(config)
            self.log(f"Initialized {type(self).__name__}")
        except Exception as e:
            self.log(
                f"Failed to initialize cog {type(self).__name__}: {e}", level="error"
            )

    def log(self, message: str, level: str = "info") -> None:
        """Log a message using the logger instance with a specified level."""
        log_method = self.LOG_LEVELS.get(level, self.logger.info)
        log_method(f"{type(self).__name__}:{message}")

    def update(self, config: dict) -> None:
        """Update existing config data with new config data."""
        raise NotImplementedError(
            "Subclasses must override the 'update' method to load config data."
        )

    def load_config(self, config: dict) -> bool:
        """Load the config data and update if necessary."""
        try:
            config_hash = gen_config_hash(config)
            quiet = self.config_hash is None

            if config_hash != self.config_hash:
                self.update(config)
                self.config_hash = config_hash
                if not quiet:
                    self.log(f"Updated {type(self).__name__} config")
                return True
            return False
        except Exception as e:
            self.log(
                f"Failed to load config for cog {type(self).__name__}: {e}",
                level="error",
            )
            return False
