import discord
from discord import member
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

from aiohttp import InvalidURL

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

    async def view_association(self, ctx, assc : AssociationObject.Association):
        async with self.bot.db.acquire() as conn:
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
                    f"The {assc.type} with this name/ID has been disbanded.")

        await self.view_association(ctx, assc)

    @commands.user_command(name="View Association", 
        guild_ids=[762118688567984151])
    async def view_other_assc(self, ctx, member : discord.Member):
        async with self.bot.db.acquire() as conn:
            psql = """
                    SELECT assc
                    FROM players
                    WHERE user_id = $1;
                    """
            if await conn.fetchval(psql, member.id) is None:
                return await ctx.respond(
                    "This person is not in an association.")
            profile = await PlayerObject.get_player_by_id(
                conn, member.id)        
        await self.view_association(ctx, profile.assc)

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
                f"Use the `/association view` command to see it!"))

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    @commands.check(Checks.is_assc_officer)
    async def edit(self, ctx,
            description : Option(str,
                description="Change the association's description",
                required=False),
            icon : Option(str,
                description="Change the association's icon",
                required=False),
            lock : Option(str,
                description=(
                    "Lock/Unlock the association from players joining via "
                    "the /join command"),
                required=False,
                choices=[OptionChoice("Lock"), OptionChoice("Unlock")]),
            level_requirement : Option(int,
                description=(
                    "Set a minimum level for players to join the association "
                    "via the /join command"),
                required=False,
                min_value=0,
                max_value=250),
            kick_member : Option(discord.Member,
                description="Remove this player from the association",
                converter=commands.MemberConverter(),
                required=False),
            transfer_ownership : Option(discord.Member,
                description="Set the association owner to this player",
                converter=commands.MemberConverter(),
                required=False),
            disband : Option(str,
                description="Disband this association",
                required=False,
                choices=[OptionChoice("Confirm Association Deletion")])):
        """Change your association's settings."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            assc = player.assc
            message = ""

            # DISBAND GUILD
            if disband is not None:
                if await assc.get_member_count(conn) > 1:
                    return await ctx.respond((
                        "You can only disband an association when you are the "
                        "last member remaining."))

                if player.guild_rank != "Leader":
                    raise Checks.IncorrectAssociationRank("Leader")

                await assc.destroy(conn)

                message += f"**{assc.name}** has been disbanded."
                return await ctx.respond(message)

            # CHANGE DESCRIPTION
            if description is not None:
                if len(description) > 256:
                    message += (
                        f"Description not changed as it is above the 256 "
                        f"character limit. {len(description)} characters "
                        f"were given.\n")
                else:
                    await assc.set_description(conn, description)
                    message += "Description updated.\n"

            # CHANGE ICON
            if icon is not None:
                try:
                    await assc.set_icon(conn, icon)
                except (InvalidURL, Checks.InvalidIconURL):
                    message += "Icon left unchanged as URL was invalid."
                else:
                    message += "Icon updated.\n"

            # CHANGE LOCK
            if lock == "Lock":
                await assc.lock(conn)
                message += f"Locked association from new players\n"
            if lock == "Unlock":
                await assc.unlock(conn)
                message += f"Unlocked association to new players.\n"

            # CHANGE LEVEL REQUIREMENT
            if level_requirement is not None:
                await assc.set_assc_lvl_req(conn, level_requirement)
                message += (
                    f"Minimum Level to join set to {level_requirement}.\n")

            # KICK A MEMBER
            if kick_member is not None:
                player = await PlayerObject.get_player_by_id(
                    conn, kick_member.id)
                if player.assc.id != assc.id:
                    message += (
                        f"No players kicked as they are not in this "
                        f"association.\n")
                elif player.guild_rank in ("Officer", "Leader"):
                    message += (
                        f"No players kicked as they are a high ranking member."
                        "\n")
                else:
                    await player.leave_assc(conn)
                    await kick_member.send(
                        f"You have been removed from **{assc.name}** by "
                        f"{ctx.author.name}.")
                    message += f"Kicked member {kick_member.name}.\n"

            # TRANSFER LEADERSHIP
            if transfer_ownership is not None:
                player = await PlayerObject.get_player_by_id(
                    conn, transfer_ownership.id)
                if player.assc.id != assc.id:
                    message += (
                        f"Leadership unchanged as target is not in this "
                        f"association.\n")
                elif player.guild_rank not in ("Officer", "Leader"):
                    message += (
                        f"Leadership unchanged as target is not a high ranking "
                        "association member.\n")
                else:
                    await assc.set_leader(conn, transfer_ownership.id)
                    message += (
                        f"Association ownership changed to "
                        f"{transfer_ownership.name}\n")

            # SEND MESSAGE ON COMPLETION
            if len(message) == 0:
                await ctx.respond("You made no changes to your association.")
            else:
                embed = discord.Embed(
                    title=f"Changes made to {assc.name}",
                    description=f"```{message}```",
                    color=Vars.ABLUE)
                await ctx.respond(embed=embed)

    
    # TODO: invite command and UserCommand
    # promote/demote
    # leave guild
    # contribute money
    # exclusive commands
    # join command


def setup(bot):
    bot.add_cog(Associations(bot))