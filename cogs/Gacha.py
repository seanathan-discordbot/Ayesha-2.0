import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands

from Utilities import Checks, Vars, PlayerObject
from Utilities.Finances import Transaction

class Gacha(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Gacha is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def summon(self, ctx, 
            pulls : Option(int,
                description="Do up to 10 pull at once!",
                required=False,
                min_value=1,
                max_value=10,
                default=1)):
        """Spend 1 rubidics to get a random acolyte or weapon."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.rubidics < pulls:
                raise Checks.NotEnoughResources("rubidics", 
                    pulls, player.rubidics)
            
            await ctx.respond(f"You have {player.rubidics} and are at {player.pity_counter} pulls.")


def setup(bot):
    bot.add_cog(Gacha(bot))