# Modular Discord Bot Framework

A template for Discord bots based on `pycord` with built-in handling of config files (YAML or TOML), easy Docker packaging, and modular components powered by Cogs.

## Table of Contents

- [Building a bot with MDBF](#building-a-bot-with-mdbf)
- [Cogs](#cogs)
- [Config](#config)
- [Packaging your bot with Docker](#packaging-your-bot-with-docker)
- [Hosting your bot with Docker Compose](#hosting-your-bot-with-docker-compose)
- [Troubleshooting](#troubleshooting)

## Building a bot with MDBF

MDBF handles most of the setup for you! All you need is to write some cogs and instantiate an `MDBFBot` like so:

```python
# Import necessary modules
from discord import Intents
from mdbf.bot import MDBFBot
from mdbf.utils import locate_config

# Import your custom cogs
from cogs.example_one import ExampleCogOne
from cogs.example_two import ExampleCogTwo

# Set up bot intents
intents = Intents.default()

# Initialize the bot
bot = MDBFBot(
    name="MyBot",  # Name of the bot
    intents=intents,  # Discord intents
    config_path=locate_config(),  # Path to the config file, which can be auto-discovered with a utility function
    cogs=[ExampleCogOne, ExampleCogTwo],  # List of cogs
    cog_configs={"ExampleCogOne": "ex_one", "ExampleCogTwo": "ex_two"},  # Config section mappings for cogs
    chunk_guilds_at_startup=False,  # Optional argument
)

# Start the bot
bot.serve()
```

You can pass any other arguments to an `MDBFBot` that you can to a normal `pycord` bot.

## Cogs

MDBF is built on top of Cogs. A Cog can be thought of as an isolated set of functionality that pertains to a specific job performed by the bot. For example, you might have a ReactionCog that reacts to user messages based on their content, or a ModCog that handles moderation actions. Ideally, only the functionality that a specific Cog actually needs to perform should be included in that Cog. A ModCog shouldn't also be handling reaction roles, for example. Each Cog gets its own section in the config, if you define one, and holds its own state. Cogs can be reloaded individually without interrupting each other. To make a new Cog for your bot, define a subclass of the `BaseCog` in `mdbf.cogs`. Here's a simple Cog that reacts to messages containing the bot's name:

```python
import re

import discord

from mdbf.cogs import BaseCog


class SimpleCog(BaseCog):
    # This method handles updating Cog state based on config data
    def __update(self, config: dict) -> None:
        self.emoji = config["emoji"]

    @BaseCog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return # Ignore messages from other bots!

        content = message.content.lower() # We don't care about case
        if (
            message.guild.get_member(self.bot.user.id).nick # If this bot has a nickname...
            and message.guild.get_member(self.bot.user.id).nick.lower() in content # And it's in the message...
        ) or (self.bot.user.name.lower() in content): # Or its global name is in the message...
                await message.add_reaction(self.emoji) # React with the configured emoji
```

The SimpleCog's config section, if named "simple", would look like this:

- In YAML:

  ```yaml
  simple:
    emoji: ✨
  ```

- In TOML:

  ```toml
  [simple]
  emoji = "✨"
  ```

- Or in JSON:

  ```json
  {
    "simple": {
      "emoji": "✨"
    }
  }
  ```

Which would configure it to react with sparkles to its name being mentioned. More complex behavior can be modelled using all of the tools available to normal `pycord` Cogs.

## Config

MDBF Handles config reloads via an application command: `/reload`. It can only be run by configured admins, and rather than restarting the whole bot, it triggers a reload of each Cog individually. This is the main advantage of MDBF over just using `pycord`: Configs are handled fully by MDBF, and exposed as normal Python dictionaries to Cogs. If the config hasn't changed, no reload is performed, and if it has, the Cog can reload itself in real time without interrupting other cogs.

Each Cog needs to implement its own `update` function, which should re-assign any values read from config, and perform any other config dependent initialization logic, such as compiling regexes, caching images from URLs, connecting to databases, etc. This method is automatically called by MDBF when a config change is detected during a `reload`, and at Cog initialization.

Configs can be provided at the following paths: `config.yaml` or `config.yml` (YAML format), `config.toml` (TOML format), or `config.json` (JSON format). Only one config file should be provided! There is also one "config" value that must be passed as an environment variable: `BOT_TOKEN`. The only config option present in MDBF itself is `admins`, which is a list of user IDs for users who should be considered "admins" of the bot. They will be able to reload the config, and you can use the `check_admin` function provided by your MDBFBot instance in your Cogs to alter behavior (for example, an `if` statement in an application command to send an error instead of executing a command when run by a non-admin). Any other configuration is determined by your implementation.

## Resources

- [Pycord Documentation](https://docs.pycord.dev/)
- [Discord Developer Console](https://discord.com/developers/applications)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
