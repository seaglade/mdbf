# Modular Discord Bot Framework

A template for Discord bots based on `pycord` with built-in handling of config files (YAML or TOML), easy Docker packaging, and modular components powered by Cogs.

## Building a bot with MDBF

MDBF handles most of the setup for you! All you need is to write some cogs and instantiate an `MDBFBot` like so:

```python
from discord import Intents
from mdbf.bot import MDBFBot
from mdbf.utils import locate_config

from cogs.example_one import ExampleCogOne
from cogs.example_two import ExampleCogTwo

intents = Intents.default()

bot = MDBFBot(
    name="MyBot",
    intents=intents,
    config_path=locate_config(),
    cogs=[ExampleCogOne, ExampleCogTwo],
    cog_configs={"ExampleCogOne": "ex_one", "ExampleCogTwo": "ex_two"},
    chunk_guilds_at_startup=False,
)

bot.serve()
```

You can pass any other arguments to an `MDBFBot` that you can to a normal `pycord` bot.

### Cogs

MDBF is built on top of Cogs. A Cog can be thought of as an isolated set of functionality that pertains to a specific job performed by the bot. For example, you might have a ReactionCog that reacts to user messages based on their content, or a ModCog that handles moderation actions. Ideally, only the functionality that a specific Cog actually needs to perform should be included in that Cog. A ModCog shouldn't also be handling reaction roles, for example. Each Cog gets its own section in the config, if you define one, and holds its own state. Cogs can be reloaded individually without interrupting each other. To make a new Cog for your bot, define a subclass of the `BaseCog` in `mdbf.cogs`. Here's a simple Cog that reacts to messages containing the bot's name:

```python
import re

import discord

from mdbf.cogs import BaseCog


class SimpleCog(BaseCog):
    def update(self, config: dict) -> None:
        self.emoji = config["emoji"]

    @BaseCog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return # Ignore messages from bots!

        content = message.content.lower() # We don't care about case
        if (
            message.guild.get_member(self.bot.user.id).nick # If this bot has a nickname...
            and message.guild.get_member(self.bot.user.id).nick.lower() in content # And it's in the message...
        ) or (self.bot.user.name.lower() in content): # Or its global name is in the message...
                await message.add_reaction(self.emoji) # React with the configured emoji
```

The SimpleCog's config section, if named "simple", would look like this:

```yaml
simple:
  emoji: ✨
```

Which would configure it to react with sparkles to its name being mentioned. More complex behavior can be modelled using all of the tools available to normal `pycord` Cogs.

### Config

MDBF Handles config reloads via an application command: `/reload`. It can only be run by configured admins, and rather than restarting the whole bot, it triggers a reload of each Cog individually. This is the main advantage of MDBF over just using `pycord`: Configs are handled fully by MDBF, and exposed as normal Python dictionaries to Cogs. If the config hasn't changed, no reload is performed, and if it has, the Cog can reload itself in real time without interrupting other cogs.

Each Cog needs to implement its own `update` function, which should re-assign any values read from config, and perform any other config dependent initialization logic, such as compiling regexes, caching images from URLs, connecting to databases, etc. This method is automatically called by MDBF when a config change is detected during a `reload`, and at Cog initialization.

Configs can be provided at the following paths: `config.yaml` or `config.yml` (YAML format) or `config.toml` (TOML format). Only one config file should be provided! There are also two "config" values that must be passed as environment variables: `BOT_TOKEN` and `BOT_GUILD_ID`. The only config option present in MDBF itself is `admins`, which is a list of user IDs for users who should be considered "admins" of the bot. They will be able to reload the config, and you can use the `check_admin` function provided by your MDBFBot instance in your Cogs to alter behavior (for example, an `if` statement in an application command to send an error instead of executing a command when run by a non-admin). Any other configuration is determined by your implementation.

### Packaging your bot with Docker

This repo includes a `Dockerfile.example` file that can be used to build your bot, assuming you use UV for project management (which you should, because it's great!) and put your Cogs in the `./cogs/` directory and your bot initialization in `./main.py`, both relative to your project root. If that's the case, you can just build the image with your favorite CICD tool and run the image wherever you want to host your bot.

### Hosting your bot with Docker Compose

An instance of a bot built on MDBF **can only exist in a single guild!**. This is intentional, to avoid the need to manage state across multiple servers. I'm open to advice on how to implement multi-guild functionality, but it isn't planned since all of my own bots are specific to certain servers. You can also just host multiple instances of the same bot in different guilds, if you want. The following mini-guide explains how to set up an individual instance using Docker Compose.

1. Build the docker image. I currently use OneDev for CICD, but you can do it manually, with GitHub Actions, with Drone... In the next steps I'll use `bot:latest` to refer to the image, but you should replace that with wherever your image is located.
2. Make a bot in the Discord Developer Console. Copy its token. I'll use `<token>` where you should paste it.
3. Copy the guild ID of the server your bot will run in. Again, a single instance currently **cannot function in multiple servers!** Paste it where you see `<guild_id>`.
4. Make a `docker-compose.yml` like this:

```yaml
services:
  bot:
    image: bot:latest
    restart: unless-stopped
    environment:
      BOT_TOKEN: <token>
      BOT_GUILD_ID: <guild_id>
    volumes:
      - ./config/:/app/config/
```

5. Make a folder named `config` and put a new file in it called `config.yml`, `config.yaml` or `config.toml`. If you bind the file directly, hot reloads (via `/reload`) will not work, since docker will not update the contents of the file when they change on the host. Add any config needed for your bot's Cogs.
6. Add the bot to your server via the Discord Developer Console.
7. Launch the stack with `docker compose up -d`. If you want to tail the logs, use `docker compose logs -f`. Don't launch the bot in production without `-d`! If you do, it will go down if you close your terminal, control-c the process, etc!
8. Assuming you've done everything right up to this point, your bot is now ready to use! The sky is the limit.
