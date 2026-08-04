from discord import Intents

from cogs.example import ExampleCog
from mdbf.bot import MDBFBot


if __name__ == "__main__":
    bot = MDBFBot(
        cogs=[ExampleCog],
        intents=Intents.default(),
    )

    bot.serve()
