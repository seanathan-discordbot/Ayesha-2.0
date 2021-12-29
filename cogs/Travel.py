import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

class Travel(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Travel is ready.")


def setup(bot):
    bot.add_cog(Travel(bot))