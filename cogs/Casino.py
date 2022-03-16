import discord
from discord import Option

from discord.ext import commands

import asyncio
import random

from Utilities import Vars

class Casino(commands.Cog):
    """Casino text"""

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        self.check_for_reminders.start()
        print("Casino is ready.")

    # COMMANDS



def setup(bot):
    bot.add_cog(Casino(bot))