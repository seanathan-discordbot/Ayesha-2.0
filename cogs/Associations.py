import discord
from discord import member
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

from aiohttp import InvalidURL
import random

from Utilities import AcolyteObject, AssociationObject, Checks, PlayerObject, Vars
from Utilities.ConfirmationMenu import ConfirmationMenu
from Utilities.Finances import Transaction

class InviteMenu(ConfirmationMenu):
    def __init__(self, author, target : discord.Member):
        self.target = target
        super().__init__(author)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.target.id

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

    b = discord.commands.SlashCommandGroup("brotherhood",
        "Association commands exclusive to brotherhood members", 
        guild_ids=[762118688567984151])

    c = discord.commands.SlashCommandGroup("college",
        "Association commands exclusive to college members", 
        guild_ids=[762118688567984151])

    g = discord.commands.SlashCommandGroup("guild",
        "Association commands exclusive to guild members", 
        guild_ids=[762118688567984151])

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
            try:
                assc_leader = await ctx.bot.fetch_user(assc.leader)
            except discord.HTTPException:
                assc_leader = str(assc.leader)
            assc_members = await assc.get_member_count(conn)
            assc_capacity = assc.get_member_capacity()
            assc_level, progress = assc.get_level(give_graphic=True)
            member_list = await assc.get_all_members(conn)
            try:
                champ_list = await assc.get_champions(conn)
            except Checks.NotInSpecifiedAssociation:
                pass

        # Create embed - similar to the one shown in profile
        mainpage = discord.Embed(            
            title=f"{assc.type}: {assc.name}",
            color=Vars.ABLUE)
        mainpage.set_thumbnail(url=assc.icon)
        mainpage.add_field(name="Leader", value=assc_leader)
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

        embeds = [mainpage] # Multiple embeds need to be paginated

        # Create an embed containing champion info if brotherhood
        if assc.type == "Brotherhood":
            championpage = discord.Embed(title=f"{assc.name}'s Champions")
            for i, champion in enumerate(champ_list):
                try:
                    championpage.add_field(name=f"Champion {i+1}",
                        value = (
                            f"Name: {champion.char_name}\n"
                            f"ATK/CRIT: `{champion.get_attack()}`/"
                            f"`{champion.get_crit()}`%\n"
                            f"HP/DEF: `{champion.get_hp()}`/"
                            f"`{champion.get_defense()}`%"))
                except AttributeError:
                    championpage.add_field(name=f"Champion {i+1}", 
                        value = "None")
            championpage.set_footer(text=(
                "If a champion is 'None', ask an officer to add one with the "
                "'/brotherhood champion' command!"))
            embeds.append(championpage)

        # Create embed list containing all the member information
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
            # Don't show disbanded guilds
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
            change_rank : Option(discord.Member,
                description=(
                    "Change one of your members' ranks. Select the rank in "
                    "the 'rank_to' parameter."),
                converter=commands.MemberConverter(),
                required=False),
            rank_to : Option(str,
                description="The rank you are changing the `change_rank` to",
                required=False,
                choices=[
                    OptionChoice("Officer"), 
                    OptionChoice("Adept"),
                    OptionChoice("Member")]),
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
                target = await PlayerObject.get_player_by_id(
                    conn, kick_member.id)
                if target.assc.id != assc.id:
                    message += (
                        f"No players kicked as they are not in this "
                        f"association.\n")
                elif target.guild_rank in ("Officer", "Leader"):
                    message += (
                        f"No players kicked as they are a high ranking member."
                        "\n")
                else:
                    await target.leave_assc(conn)
                    await kick_member.send(
                        f"You have been removed from **{assc.name}** by "
                        f"{ctx.author.name}.")
                    message += f"Kicked member {kick_member.name}.\n"

            # PROMOTE/DEMOTE
            if change_rank is not None and rank_to is not None:
                if player.guild_rank != "Leader":
                    raise Checks.IncorrectAssociationRank("Leader")

                target = await PlayerObject.get_player_by_id(
                    conn, change_rank.id)
                if target.assc.id != assc.id:
                    message += (
                        f"Player rank unchanged as they are not in this "
                        f"association.\n")
                elif target.disc_id == assc.leader:
                    message += (
                        "Player rank unchanged as they are the association "
                        "leader.\n")
                else:
                    await target.set_association_rank(conn, rank_to)
                    await change_rank.send(
                        f"Your rank in **{assc.name}** has been changed to "
                        f"**{rank_to}**.")
                    message += f"Set {change_rank.name}'s rank to {rank_to}.\n"

            # TRANSFER LEADERSHIP
            if transfer_ownership is not None:
                if player.guild_rank != "Leader":
                    raise Checks.IncorrectAssociationRank("Leader")

                target = await PlayerObject.get_player_by_id(
                    conn, transfer_ownership.id)
                if target.assc.id != assc.id:
                    message += (
                        f"Leadership unchanged as target is not in this "
                        f"association.\n")
                elif target.disc_id == assc.leader:
                    message += (
                        "Leadership unchanged as target is already leader.\n")
                elif target.guild_rank not in ("Officer", "Leader"):
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

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    @commands.check(Checks.is_assc_officer)
    async def invite(self, ctx, target : Option(discord.Member,
            description="The person you are inviting to your association",
            converter=commands.MemberConverter())):
        """Invite a player to your association"""
        async with self.bot.db.acquire() as conn:
            profile = await PlayerObject.get_player_by_id(conn, target.id)
            if not profile.assc.is_empty:
                return await ctx.respond(
                    "This player is already in an association.")
            # target is eligible for invitation
            author = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            assc = author.assc
            embed = discord.Embed(color=Vars.ABLUE)
            embed.add_field(name=f"Invitation to {assc.name}",
                value=(
                    f"{target.mention}, {ctx.author.mention} is inviting you "
                    f"to join their {assc.type}."))
            view = InviteMenu(author=ctx.author, target=target)
            msg = await ctx.respond(target.mention, embed=embed, view=view)
            await view.wait()
            if view.value is None:
                await ctx.respond("Timed out.")
            elif view.value:
                await profile.join_assc(conn, assc.id)
                await ctx.respond((
                    f"{target.mention}, welcome to {assc.name}! Do "
                    f"`/association view` to see it!"))
            else:
                await ctx.respond("They declined your offer.")
            await msg.delete_original_message()
        
    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_association)
    async def join(self, ctx, association : Option(int,
            description="the ID of the association you want to join")):
        """Join an open association"""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            assc = await AssociationObject.get_assc_by_id(conn, association)
            if assc.join_status != "open":
                return await ctx.respond(
                    "This association is closed to new players.")
            if player.level < assc.lvl_req:
                return await ctx.respond(
                    f"You must be level `{assc.lvl_req}` to join this "
                    f"association. You are currently level `{player.level}`.")
            # Otherwise they can join the association
            await player.join_assc(conn, assc.id)
            await ctx.respond((
                f"You have successfully joined **{assc.name}**! Use the "
                f"`/association view` command to see it!"))

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    async def leave(self, ctx):
        """Leave your current association."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.guild_rank == "Leader":
                return await ctx.respond(
                    "You are the leader; you cannot leave!")
            await player.leave_assc(conn)
            await ctx.respond("You left your association.")

    @a.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_association)
    async def contribute(self, ctx, donation : Option(int,
            description="The amount of gold you are donating",
            min_value=1,
            max_value=10000000)):
        """Contribute money to the strength of your association. Each level costs 1,000,000 gold."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.assc.get_level() >= 10:
                return await ctx.respond(
                    f"**{player.assc.name}** is already at its maximum level!")
            # Decrease donation amount so that they don't "over-donate"
            to_max_level = 10000000 - player.assc.xp
            donation = to_max_level if to_max_level < donation else donation
            purchase = await Transaction.calc_cost(conn, player, donation)
            if purchase.paying_price > player.gold:
                raise Checks.NotEnoughGold(purchase.paying_price, player.gold)
            # Complete the transaction
            await player.assc.increase_xp(conn, donation)
            print_tax = await purchase.log_transaction(conn, "purchase")
            await ctx.respond(
                f"You donated `{donation}` gold to your association, "
                f"increasing its xp to `{player.assc.xp}`. "
                f"**{player.assc.name}** is level {player.assc.get_level()}. "
                f"{print_tax}")



    # ------------------------------------------
    # ----- BROTHERHOOD EXCLUSIVE COMMANDS -----
    # ------------------------------------------

    @b.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @cooldown(1, 3600, BucketType.user)
    async def steal(self, ctx):
        """Steal up to 5% of a random player's gold."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if random.randint(1,100) >= 20 + player.assc.get_level()*5:
                return await ctx.respond("You were caught and had to flee.")

            possible_nums = await PlayerObject.get_player_count(conn)
            victim_num = random.randint(1, possible_nums-1)

            try: # Gets a random player using their unique ID
                victim = await PlayerObject.get_player_by_num(conn, victim_num)
            except Checks.NonexistentPlayer:
                # Due to poor planning in Ayesha 1.0 Alpha, some nums 
                # don't actually exist. This compensates for that
                await player.give_gold(conn, 100)
                return await ctx.respond(
                    f"You stole `100` gold from a random guy.")

            if victim.disc_id == player.disc_id: # Steal from themselves
                return await ctx.respond(
                    "You stole gold from a person's pocket, but then realized "
                    "that the pocket you stole from was yours! You gained `0` "
                    "gold.")

            amount_stolen = 50 if victim.gold < 1000 else int(victim.gold / 20)
            await victim.give_gold(conn, amount_stolen * -1)
            if player.occupation == "Engineer": # Occupation bonus
                amount_stolen *= 2
            await player.give_gold(conn, amount_stolen)
            await ctx.respond(
                f"You stole `{amount_stolen}` gold from {victim.char_name}.")

    @b.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_assc_officer)
    async def champion(self, ctx, 
            slot : Option(int,
                description=(
                    "The order in battle you are putting this champion into."),
                min_value=1,
                max_value=3),
            champion : Option(discord.Member,
                description="The person you are making champion",
                converter=commands.MemberConverter(),
                required=False)):
        """Assign someone to be a champion of your brotherhood."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            assc = player.assc

            if champion is None: # Unequip champion in given slot
                await assc.remove_champion(conn, slot)
                await ctx.respond(f"Removed the champion in slot {slot}.")
            else:
                target = await PlayerObject.get_player_by_id(conn, champion.id)
                if target.assc.id != player.assc.id:
                    return await ctx.respond(
                        "This player is not in your association.")
                current = await assc.get_champions(conn)
                if target.disc_id in [player.disc_id for player in current]:
                    return await ctx.respond(
                        "This player is already one of your champions.")
                await assc.set_champion(conn, target.disc_id, slot)
                await ctx.respond(
                    f"Added {target.char_name} to your the brotherhood's "
                    f"roster of champions.")

    # TODO: Implement area attack when a combat system is developed



    # --------------------------------------
    # ----- COLLEGE EXCLUSIVE COMMANDS -----
    # --------------------------------------

    @c.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_college)
    @cooldown(1, 14400, BucketType.user)
    async def usurp(self, ctx):
        """Make a political play for power, gaining a few gravitas."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            chance = random.randint(1,4)
            gravitas = 5 if player.occupation == "Engineer" else 0
            gravitas += player.assc.get_level()
            if chance == 1: # Failure
                gravitas -= random.randint(16, 25)
                message = (
                    f"Your political play was wildly unpopular with the "
                    f"people of {player.location}. You lost `{gravitas}` "
                    f"gravitas.")
            elif chance == 2: # Big success
                gravitas += random.randint(12, 25)
                message = (
                    f"Your maneuver was received with raucous applause from "
                    f" the people of {player.location}. You gained "
                    f"`{gravitas}` gravitas.")
            else:
                gravitas += random.randint(3, 10)
                message = (
                    f"Your speech turned some heads but most of the people of "
                    f"{player.location} are apathetic to your rhetoric. You "
                    f"gained `{gravitas}` gravitas.")
            
            await player.give_gravitas(conn, gravitas)
            await ctx.respond(message)



    # ------------------------------------
    # ----- GUILD EXCLUSIVE COMMANDS -----
    # ------------------------------------

    @g.command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @cooldown(1, 7200, BucketType.user)
    async def invest(self, ctx, capital : Option(int,
            description="The amount of money you are investing",
            min_value=100,
            max_value=250000)):
        """Invest in a nearby project and gain/lose some money."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.gold < capital:
                raise Checks.NotEnoughGold(capital, player.gold)
            
            # Determine the return
            bonus_occ = player.occupation == "Engineer"
            multiplier = random.randint(0, 21500) / 10000.0 # up to 2.15x
            print(multiplier)
            return_amt = int(capital * multiplier)
            return_amt = int(return_amt * 1.25) if bonus_occ else return_amt

            # Pick random things to display to player
            projects = ("museum", "church", "residence", 
                "fishing company", "game company", "guild", "boat", 
                "road construction", "cooperative", "ponzi scheme", "MLM",
                "non-fungible token", "animal herd", "mercenary band")
            project = random.choice(projects)

            # Determine if loss or gain
            capital_gains = return_amt - capital
            if capital_gains > 0: # Player made money, tax it
                sale = await Transaction.create_sale(
                    conn, player, capital_gains)
                print_tax = await sale.log_transaction(conn, "sale")
                message = (
                    f"You invested `{capital}` gold in a {project} and made a "
                    f"return of `{return_amt}`. {print_tax}")
            else:
                await player.give_gold(conn, capital_gains)
                message = (
                    f"You invested `{capital}` gold in a {project} and made a "
                    f"return of `{return_amt}`. Since you lost money, you "
                    f"were not taxed.")
            await ctx.respond(message)

    # guild bank account


def setup(bot):
    bot.add_cog(Associations(bot))