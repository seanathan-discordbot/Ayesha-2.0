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
        # Load Information
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            assc = player.assc
            assc_leader = await ctx.bot.fetch_user(assc.leader)
            assc_members = await assc.get_member_count(conn)
            assc_capacity = assc.get_member_capacity()
            assc_level, progress = assc.get_level(give_graphic=True)

        # Create embed - similar to profile
        mainpage = discord.Embed(            
            title=f"{assc.type}: {assc.name}",
            color=Vars.ABLUE)
        mainpage.set_thumbnail(url=assc.icon)
        mainpage.add_field(name="Leader", value=assc_leader.mention)
        mainpage.add_field(name="Members", 
            value=f"{assc_members}/{assc_capacity}")
        mainpage.add_field(name="Level", value=assc_level)
        mainpage.add_field(name="EXP Progress", value=progress)
        mainpage.add_field(name="Base", value=assc.base)
        if assc.join_status != "open":
            mainpage.add_field(name=
                f"This {assc.type} is closed to new members.",
                value=assc.desc,
                inline=False)
        else:
            mainpage.add_field(name=(
                f"This {assc.type} is open to new members at or "
                f"above level {assc.lvl_req}."),
                value=assc.desc,
                inline=False)
        mainpage.set_footer(text=f"{assc.type} ID: {assc.id}")

        await ctx.respond(embed=mainpage)

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_association)
    async def create(self, ctx,
            name : Option(str, description="The name of your association"),
            atype : Option(str,
                description="The type of association you are founding",
                choices = [
                    OptionChoice("Brotherhood"),
                    OptionChoice("College"),
                    OptionChoice("Guild")]),
            base : Option(str,
                description="Your association's headquarters location",
                choices = [OptionChoice(t) for t in Vars.TRAVEL_LOCATIONS])):
        """Create a new association for 20,000 gold."""
        if len(name) > 32:
            raise Checks.ExcessiveCharacterCount(limit=32)
        
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            purchase = await Transaction.calc_cost(conn, player, 20000)
            if purchase.paying_price > player.gold:
                raise Checks.NotEnoughGold(purchase.paying_price, player.gold)
            # Create the guild
            assc = await AssociationObject.create_assc(
                conn, name, atype, base, player.disc_id)
            await purchase.log_transaction(conn, "purchase")
            await ctx.respond((
                f"Founded the **{assc.type} {assc.name}**! "
                f"Use the `/association view` command to see it!`"))

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    @commands.check(Checks.is_assc_officer)
    async def edit(self, ctx):
        """Change your association's settings."""
        await ctx.respond("3")


def setup(bot):
    bot.add_cog(Associations(bot))