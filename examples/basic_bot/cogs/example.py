from discord import ApplicationContext

from mdbf.cogs.base import BaseCog


class ExampleCog(BaseCog):
    def __update(self, config: dict) -> None:
        self.emoji = config["emoji"]

    @BaseCog.slash_command(
        name="emoji",
        description="Responds with the configured emoji",
    )
    async def ping(self, ctx: ApplicationContext) -> None:
        await ctx.interaction.response.send_message(self.emoji)
