from os import environ
from typing import ValuesView, cast

import discord
from discord.ext.commands import Bot
import logging

from .cogs import BaseCog
from .utils import gen_config_hash, locate_config, read_config


class MDBFBot(Bot):
    """An instance of a custom pycord bot that can be used with MDBF cogs and configs"""

    def __init__(
        self,
        cogs: list[type[BaseCog]],
        config_path: str = locate_config(),
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self._config_path = config_path

        # Validate required environment variables
        bot_token = environ.get("BOT_TOKEN")
        if not bot_token:
            raise ValueError("Environment variable BOT_TOKEN is required.")

        # Initialize logger
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.INFO)

        # Load the initial config and set up cogs
        # Unlike in _reload, an exception here should be fatal, so there is no try/catch being used
        config = read_config(self._config_path)
        self._config_hash = gen_config_hash(config)
        admins = config.get("admins")
        if not admins:
            raise ValueError("The 'admins' list is required in the configuration.")
        else:
            self._admins = admins
        for cog in cogs:
            cog_config = (
                # Cogs with no config key or whose key is not in
                # the config data get an empty dict as "config"
                config.get(cog.config_key, {}) if cog.config_key is not None else {}
            )
            self.add_cog(cog(self, cog_config, self.__logger))

    def log(
        self,
        message: str,
        level: int = logging.INFO,
    ) -> None:
        """Log a message using the logger instance with a specified level."""
        self.__logger.log(level, f"{type(self).__name__}:{message}")

    def _reload(self) -> list[str]:
        """Check for changes to the bot configuration and load new config if there are changes"""
        config = read_config(self._config_path)
        config_hash = gen_config_hash(config)
        if config_hash != self._config_hash:
            admins = config.get("admins")
            if not admins:
                raise ValueError(
                    "The 'admins' list is required in the configuration.",
                )
            else:
                self._admins = admins

            updated = []
            for cog in cast(ValuesView[BaseCog], self.cogs.values()):
                # Cogs without config keys do not have config to reload
                # and as such can be skipped.
                if cog.config_key is not None:
                    did_update = cog.load_config(config.get(cog.config_key, {}))
                    if did_update:
                        updated.append(type(cog).__name__)
            self._config_hash = config_hash
            return updated
        else:
            return []

    def check_admin(self, user: discord.User | discord.Member) -> bool:
        """Check whether a user is an admin."""
        return user.id in self._admins

    def serve(self) -> None:
        """Start serving the bot instance."""

        @self.listen(once=True)
        async def on_ready() -> None:
            self.log(f"Bot is ready (logged in as {self.user})")

        @self.slash_command(
            name="reload",
            description="Reloads the bot's configuration",
        )
        async def reload_command(ctx: discord.ApplicationContext) -> None:
            if self.check_admin(ctx.author):
                try:
                    self.log(
                        f"{ctx.author.name} requested a config reload, using file {self._config_path}..."
                    )
                    updated = self._reload()
                    if updated:
                        await ctx.interaction.response.send_message(
                            f"Configuration reloaded for cogs: {', '.join(updated)}",
                            ephemeral=True,
                        )
                    else:
                        await ctx.interaction.response.send_message(
                            "No configuration changes detected", ephemeral=True
                        )
                except Exception as e:
                    self.log(f"Failed to reload configuration: {e}", logging.ERROR)
                    await ctx.interaction.response.send_message(
                        "An error occurred while reloading the configuration.",
                        ephemeral=True,
                    )
            else:
                self.log(
                    f"{ctx.author.name} requested a config reload, but they are not an admin",
                    logging.WARNING,
                )
                await ctx.interaction.response.send_message(
                    "You do not have permission to use this command", ephemeral=True
                )

        self.run(environ.get("BOT_TOKEN"))
