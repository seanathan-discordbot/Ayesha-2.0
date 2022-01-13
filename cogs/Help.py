import discord
from discord import Option, OptionChoice

from discord.ext import commands

from Utilities import Checks, Vars

class Help(commands.Cog):
    """Get help with the bot!"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Help is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    async def help(self, ctx):
        """Get help with the bot!"""
        await ctx.respond("TBD")


def setup(bot):
    bot.add_cog(Help(bot))