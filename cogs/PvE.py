import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

from Utilities import Checks, CombatObject, PlayerObject, Vars
from Utilities.CombatObject import CombatMenu

class PvE(commands.Cog):
    """Association Text"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvE is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.max_concurrency(1, BucketType.user)
    async def pve(self, ctx,
            level : Option(int,
                description="The difficulty level of your opponent",
                min_value=1,
                max_value=25)):
        """Fight an enemy for gold, xp, and items!"""
        async with self.bot.db.acquire() as conn:
            author = await PlayerObject.get_player_by_id(conn, ctx.author.id)
        # Create belligerents
        player = CombatObject.Belligerent.load_player(player=author)
        boss = CombatObject.Belligerent.load_boss(difficulty=level)

        # Set up combat display and view
        embed = discord.Embed(
            title=f"{player.name} vs. {boss.name}",
            color=Vars.ABLUE)
        embed.add_field(
            name=f"{player.name}'s Stats",
            value = (
                f"ATK: `{player.attack}`\n"
                f"CRIT: `{player.crit}%`\n"
                f"HP: `{player.current_hp}`\n"
                f"DEF: `{player.defense}`\n"))
        embed.add_field(
            name=f"{boss.name}'s Stats",
            value = (
                f"ATK: `{boss.attack}`\n"
                f"CRIT: `{boss.crit}%`\n"
                f"HP: `{boss.current_hp}`\n"
                f"DEF: `{boss.defense}`\n"))
        embed.add_field(
            name="Your move", value=f"Turn `0`", inline=False)

        # Apparently the way views are setup necessitate that the view 
        # handles everything, unless I want to repeatedly make new ones
        view = CombatMenu(author=ctx.author, player1=player, player2=boss)
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(PvE(bot))