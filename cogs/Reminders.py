import discord
from discord import Option, OptionChoice

from discord.ext import commands, tasks

import asyncio
import asyncpg
import time

from Utilities import Vars


class Reminders(commands.Cog):
    """Reminders text"""

    def __init__(self,bot):
        self.bot = bot

    @tasks.loop(seconds=15.0)
    async def check_for_reminders(self):
        now = int(time.time())
        # Function to get all reminders
    
    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Reminders is ready.")

    @commands.Cog.listener()
    def cog_unload(self):
        self.check_for_reminders.stop()
        return super().cog_unload()

    # COMMANDS