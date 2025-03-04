from os import environ

from discord.ext.commands import Cog

from ..utils import gen_config_hash


class BaseCog(Cog, guild_ids=[int(environ.get("BOT_GUILD_ID"))]):
    """Base class for all cogs in the framework. Subclasses must implement the 'update' method to load config data."""

    config_hash = None

    def log(self, message: str) -> None:
        """Log a message to the console."""
        print(f"{self.bot.name} | {self.__class__.__name__} >> {message}")

    def update(self, config: dict) -> None:
        """Update existing config data with new config data."""
        raise NotImplementedError(
            "Subclasses must override the 'update' method to load config data."
        )

    def load_config(self, config: dict) -> bool:
        """Load the config data and update if necessary."""
        # Check if the config has changed, if not we don't need to update anything
        config_hash = gen_config_hash(config)
        # Don't print if this is the first time loading
        # the config, since the init function has its own logging
        quiet = self.config_hash is None
        if config_hash != self.config_hash:
            self.update(config)
            self.config_hash = config_hash
            if not quiet:
                print(f"Updated {self.__class__.__name__} config")
            return True
        else:
            return False

    def __init__(self, bot, config: dict) -> None:
        """Initialize the cog with the bot and config data. `bot` should be an MDBFBot instance."""
        self.bot = bot  # wish I could type this but it's a circular import. It should be an MDBFBot instance.
        self.load_config(config)
        self.log(f"Initialized {self.__class__.__name__}")
