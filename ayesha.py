import discord

import logging
import sys

from Utilities import config, Vars
from Utilities.AyeshaBot import Ayesha

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=config.LOG_FILE, 
                              encoding='utf-8', 
                              mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Load Cogs
init_cogs = [
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
    "cogs.Minigames",
    "cogs.Casino",
    "cogs.Reminders",
    "cogs.Vote"
]

if "-b" in sys.argv: # Run beta version
    init_cogs.remove("cogs.Reminders")
    init_cogs.remove("cogs.Vote")

bot = Ayesha(init_cogs)
bot.run(config.TOKEN)

# Ping command
@bot.slash_command(guild_ids=[762118688567984151])
async def ping(ctx):
    """Ping to see if bot is working."""
    fmt = f"Latency is {bot.latency * 1000:.2f} ms"
    embed = discord.Embed(title="Pong!", 
                           description=fmt, 
                           color=Vars.ABLUE)
    await ctx.respond(embed=embed)