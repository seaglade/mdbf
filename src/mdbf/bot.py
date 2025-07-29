from asyncio import ensure_future
from os import environ

import discord
from discord.ext.commands import Bot
import logging

from .cogs import BaseCog
from .utils import gen_config_hash, locate_config, read_config


class MDBFBot(Bot):
    """An instance of a custom pycord bot that can be used with MDBF cogs and configs"""

    cog_configs: dict[str, str]
    config_hash: bytes | None = None
    name: str
    admins: list[int] | None = None

    async def load_config(self, path: str) -> list[str]:
        """Load and validate the bot configuration."""
        try:
            config = read_config(path)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return []

        if path != self.config_path:
            self.config_path = path

        config_hash = gen_config_hash(config)
        if config_hash != self.config_hash:
            self.admins = config.get("admins")
            if not self.admins:
                raise ValueError("The 'admins' list is required in the configuration.")

            updated = []
            for cog_name, cog_instance in self.cogs.items():
                if cog_name in self.cog_configs:
                    cog_config_section = self.cog_configs[cog_name]
                    try:
                        if cog_instance.load_config(config.get(cog_config_section, {})):
                            updated.append(cog_name)
                    except Exception as e:
                        self.logger.error(f"Failed to load config for cog {cog_name}: {e}")
            self.config_hash = config_hash
            return updated
        return []

    async def init_cogs(self, cogs: list[BaseCog]) -> None:
        """Initialize cogs with their respective configurations."""
        try:
            config = read_config(self.config_path)
            for cog in cogs:
                cog_name = cog.__name__
                cog_config = config.get(self.cog_configs.get(cog_name, {}), {})
                self.add_cog(cog(self, cog_config, self.logger))
        except Exception as e:
            self.logger.error(f"Failed to initialize cogs: {e}")

    def __init__(
        self,
        name: str,
        config_path: str,
        cogs: list[BaseCog],
        cog_configs: dict[str, str],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        # Validate required environment variables
        bot_token = environ.get("BOT_TOKEN")
        bot_guild_id = environ.get("BOT_GUILD_ID")
        if not bot_token or not bot_guild_id:
            raise ValueError("Environment variables BOT_TOKEN and BOT_GUILD_ID are required.")

        self.name = name
        self.config_path = config_path
        self.cog_configs = cog_configs

        # Initialize logger with bot's name
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        try:
            ensure_future(self.init_cogs(cogs))
            ensure_future(self.load_config(self.config_path))
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")

    async def check_admin(self, user: discord.User) -> bool:
        """Check if a user is an admin."""
        return user.id in self.admins if self.admins else False

    def serve(self) -> None:
        """Start serving the bot instance."""

        @self.listen(once=True)
        async def on_ready() -> None:
            self.logger.info(f"{self.name} is ready (logged in as {self.user})")

        @self.slash_command(
            name="reload",
            description="Reloads the bot's configuration without restarting the bot",
        )
        async def reload_command(ctx: discord.ApplicationContext) -> None:
            if await self.check_admin(ctx.author):
                try:
                    config_path = locate_config()
                    self.logger.info(
                        f"{ctx.author.name} requested a config reload, using file {config_path}..."
                    )
                    updated = await self.load_config(config_path)
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
                    self.logger.error(f"Failed to reload configuration: {e}")
                    await ctx.interaction.response.send_message(
                        "An error occurred while reloading the configuration.", ephemeral=True
                    )
            else:
                self.logger.warning(
                    f"{ctx.author.name} requested a config reload, but they are not an admin"
                )
                await ctx.interaction.response.send_message(
                    "You do not have permission to use this command", ephemeral=True
                )

        self.run(environ.get("BOT_TOKEN"))
