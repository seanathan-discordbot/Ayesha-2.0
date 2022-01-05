import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands

from Utilities import AssociationObject, Checks, PlayerObject, Vars
from Utilities.ConfirmationMenu import ConfirmationMenu
from Utilities.Finances import Transaction

class Associations(commands.Cog):
    """Association Text"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Associations is ready.")

    a = discord.commands.SlashCommandGroup("association", 
        "Commands related to coop gameplay", guild_ids=[762118688567984151])

    # COMMANDS
    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    async def view(self, ctx):
        """View the brotherhood/college/guild that you are in."""
        await ctx.respond("1")

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_association)
    async def create(self, ctx):
        """Create a new association."""
        await ctx.respond("2")

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    @commands.check(Checks.is_assc_officer)
    async def edit(self, ctx):
        """Change your association's settings."""
        await ctx.respond("3")


def setup(bot):
    bot.add_cog(Associations(bot))