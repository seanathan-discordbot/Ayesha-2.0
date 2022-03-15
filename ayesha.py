import discord
from discord.ext import commands

import logging
import traceback

import asyncpg

from Utilities import config, Vars

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=config.LOG_FILE, 
                              encoding='utf-8', 
                              mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class Ayesha(commands.AutoShardedBot):
    """Ayesha bot class with added properties"""

    def __init__(self):
        self.recent_voters = {}
        self.trading_players = {}

        super().__init__(
            command_prefix = "$",
            case_insensitive = True
        )

        # Load Cogs
        self.init_cogs = (
            "cogs.Profile",
            "cogs.Error_Handler",
            "cogs.Items",
            "cogs.Travel",
            "cogs.Gacha",
            "cogs.Occupations",
            "cogs.Associations",
            "cogs.PvE",
            "cogs.PvP",
            "cogs.Raid",
            "cogs.Offices",
            "cogs.Misc",
            "cogs.Acolytes",
            "cogs.Help",
            "cogs.Minigames"
        )

        for cog in self.init_cogs:
            try:
                self.load_extension(cog)
                print(f"Loaded cog {cog}.")
            except:
                print(f"Failed to load cog {cog}.")
                traceback.print_exc()

    def is_admin(self, ctx):
        return ctx.author.id in config.ADMINS   

    async def on_ready(self):
        gp = "Slash commands added!"
        self.loop.create_task(self.change_presence(activity=discord.Game(gp)))

        self.announcement_channel = await self.fetch_channel(
            Vars.ANNOUNCEMENT_CHANNEL)
        self.raider_role = self.announcement_channel.guild.get_role(
            Vars.RAIDER_ROLE)

        print("Ayesha is online.")

    async def on_interaction(self, interaction):
        if interaction.user.id in self.trading_players:
            return await interaction.response.send_message(
                f"Finish your trade first.")

        return await super().on_interaction(interaction)


bot = Ayesha()

# Connect to database
async def create_db_pool():
    bot.db = await asyncpg.create_pool(database = config.DATABASE['name'],
                                       user = config.DATABASE['user'],
                                       password = config.DATABASE['password'])

bot.loop.run_until_complete(create_db_pool())

# Word Chain database
async def create_dictionary_pool():
    bot.dictionary = await asyncpg.create_pool(
        database = config.DICTIONARY['name'],
        user = config.DICTIONARY['user'],
        password = config.DICTIONARY['password'])

bot.loop.run_until_complete(create_dictionary_pool())

# Ping command
@bot.slash_command(guild_ids=[762118688567984151])
async def ping(ctx):
    """Ping to see if bot is working."""
    fmt = f"Latency is {bot.latency * 1000:.2f} ms"
    embed = discord.Embed(title="Pong!", 
                           description=fmt, 
                           color=Vars.ABLUE)
    await ctx.respond(embed=embed)

bot.run(config.TOKEN)