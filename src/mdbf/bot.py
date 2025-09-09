from asyncio import ensure_future
from os import environ

import discord
from discord.ext.commands import Bot

from .cogs import BaseCog
from .utils import gen_config_hash, locate_config, read_config


class MDBFBot(Bot):
    """An instance of a custom pycord bot that can be used with MDBF cogs and configs"""

    # Map cogs to their config sections
    cog_configs = None
    config_hash = None
    name = "Bot"

    async def load_config(self, path: str) -> list[str]:
        with open(path) as file:
            config = read_config(path)
        if path != self.config_path:
            self.config_path = path
        config_hash = gen_config_hash(config)
        if config_hash != self.config_hash:
            self.admins = config["admins"]
            updated = []
            for cog in self.cogs:
                # Reload the config for each cog that has one
                if cog in self.cog_configs:
                    if self.cogs[cog].load_config(config[self.cog_configs[cog]]):
                        updated.append(cog)
            return updated
        else:
            return []

    async def init_cogs(self, cogs):
        # The config has to be manually loaded here to init the cogs
        # after that it can be reloaded via load_config instead
        config = read_config(self.config_path)
        for cog in cogs:
            name = cog.__name__
            # Some cogs don't have config options, so we need to check if the config exists
            if name in self.cog_configs:
                self.add_cog(cog(self, config[self.cog_configs[name]]))
            else:  # If the cog doesn't have config options, just pass an empty dict
                self.add_cog(cog(self, {}))

    def __init__(
        self,
        name: str,
        config_path: str,
        cogs: list[BaseCog],
        cog_configs: dict[str, str],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.name = name
        self.config_path = config_path
        # Should map cog names to their config sections, i.e. {"FilterCog": "filter", "FunCog": "fun"}
        self.cog_configs = cog_configs
        ensure_future(self.init_cogs(cogs))
        # The cogs technically already have their configs loaded here,
        # but we need to load the bot's config too. Given that the cogs check config hashes
        # to determine if they need to actually reload their configs, this shouldn't cause any
        # performance issues. They'll just skip reloading since the hash is the same.
        ensure_future(self.load_config(self.config_path))

    async def check_admin(self, usr: discord.User):
        return usr.id in self.admins

    def serve(self):
        """Start serving an MDBF bot instance"""

        @self.listen(once=True)
        async def on_ready():
            print(f"{self.name} is ready (logged in as {self.user})")

        @self.slash_command(
            name="reload",
            description="Reloads the bot's configuration without restarting the bot",
        )
        async def reload_command(ctx: discord.ApplicationContext) -> None:
            if await self.check_admin(ctx.author):
                config_path = locate_config()
                print(
                    f"{self.name} >> {ctx.author.name} requested a config reload, using file {
                        config_path}..."
                )
                updated = await self.load_config(config_path)
                if len(updated):
                    await ctx.interaction.response.send_message(
                        f"Configuration reloaded for cogs: {
                            ', '.join(updated)}",
                        ephemeral=True,
                    )
                else:
                    await ctx.interaction.response.send_message(
                        "No configuration changes detected", ephemeral=True
                    )
            else:
                print(
                    f"{self.name} >> {
                        ctx.author.name} requested a config reload, but they are not an admin"
                )
                await ctx.interaction.response.send_message(
                    "You do not have permission to use this command", ephemeral=True
                )

        self.run(environ.get("BOT_TOKEN"))
