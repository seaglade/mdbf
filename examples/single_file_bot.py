# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "mdbf>=0.4.1",
#     "py-cord>=2.8.0",
# ]
# ///

"""An example of an MDBF bot in a single file.

If you set BOT_TOKEN in your environment and provide a minimum
config file (with an admins list), you can run this bot with
`uv run single_file_bot.py` without even needing to set up a
virtual environment!
"""

from discord import ApplicationContext, Intents
from mdbf.bot import MDBFBot
from mdbf.cogs import BaseCog


# Note that, since it has no config_key defined, this cog
# does not need to implement __update()
class ExampleCog(BaseCog):
    @BaseCog.slash_command(
        name="ping",
        description="Example command",
    )
    async def ping(self, ctx: ApplicationContext) -> None:
        await ctx.interaction.response.send_message("Pong!")


if __name__ == "__main__":
    bot = MDBFBot(
        cogs=[ExampleCog],
        intents=Intents.default(),
    )

    bot.serve()
