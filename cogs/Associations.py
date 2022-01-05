import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

from Utilities import AcolyteObject, AssociationObject, Checks, PlayerObject, Vars
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

    # AUXILIARY FUNCTIONS
    def write_member_page(self, start, members):
        embed = discord.Embed(title="Association Members", color=Vars.ABLUE)
        iteration = 0
        while start < len(members) and iteration < 10:
            player = members[start]
            embed.add_field(
                name=f"{player.char_name} [{player.guild_rank}]",
                value=(
                    f"Level `{player.level}`, with `{player.get_attack()}` "
                    f"ATK, `{player.get_crit()}` CRIT, `{player.get_hp()}` HP, "
                    f"`{player.get_defense()}` DEF"),
                inline=False)
            iteration += 1
            start += 1
        return embed

    # COMMANDS
    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    async def view(self, ctx,
            name : Option(str,
                description="Search an association by name",
                required=False),
            id : Option(int,
                description="Search an association by its ID",
                required=False),
            player : Option(discord.Member,
                description="View another player's association",
                required=False,
                converter=commands.MemberConverter())):
        """View a brotherhood/college/guild's information."""
        async with self.bot.db.acquire() as conn:
            # Get the association based on the passed argument
            if name is not None:
                psql = """
                        SELECT assc_id
                        FROM associations
                        WHERE assc_name = $1;
                        """
                assc_id = await conn.fetchval(psql, name)
                if assc_id is None:
                    return await ctx.respond(
                        f"No association exists with the name **{name}**.")
                assc = await AssociationObject.get_assc_by_id(conn, assc_id)
            elif id is not None:
                assc = await AssociationObject.get_assc_by_id(conn, id)
                if assc.is_empty:
                    return await ctx.respond(
                        f"No association exists with this ID: `{id}`.")
            elif player is not None:
                psql = """
                        SELECT assc
                        FROM players
                        WHERE user_id = $1;
                        """
                if await conn.fetchval(psql, player.id) is None:
                    return await ctx.respond(
                        "This person is not in an association.")
                profile = await PlayerObject.get_player_by_id(
                    conn, player.id)
                assc = profile.assc
            else: # Get the player's association
                profile = await PlayerObject.get_player_by_id(
                    conn, ctx.author.id)
                assc = profile.assc
            if assc.leader == 767234703161294858: # TODO: This is Ayesha's ID
                return await ctx.respond(
                    "The guild with this name/ID has been disbanded.")

            # Load the rest of the information of the associaiton
            assc_leader = await ctx.bot.fetch_user(assc.leader)
            assc_members = await assc.get_member_count(conn)
            assc_capacity = assc.get_member_capacity()
            assc_level, progress = assc.get_level(give_graphic=True)
            member_list = await assc.get_all_members(conn)

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

        # Create embed list containing all the member information
        embeds = [mainpage]
        for i in range(0, len(member_list), 10):
            embeds.append(self.write_member_page(i, member_list))

        # Paginate and send association information
            paginator = pages.Paginator(pages=embeds, timeout=30)
            paginator.customize_button("next", button_label=">", 
                button_style=discord.ButtonStyle.green)
            paginator.customize_button("prev", button_label="<", 
                button_style=discord.ButtonStyle.green)
            paginator.customize_button("first", button_label="<<", 
                button_style=discord.ButtonStyle.blurple)
            paginator.customize_button("last", button_label=">>", 
                button_style=discord.ButtonStyle.blurple)
            await paginator.send(ctx, ephemeral=False)

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
        # change base
        # desc
        # icon
        # lock
        # level req
        # promote, demote
        # transfer ownership
        # kick
        # delete
        await ctx.respond("3")

    # TODO: invite command and UserCommand
    # leave guild
    # contribute money
    # list of members
    # exclusive commands
    # join command


def setup(bot):
    bot.add_cog(Associations(bot))