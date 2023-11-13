import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

from aiohttp import InvalidURL
from datetime import datetime
import asyncio
import random
import schedule
import time

from Utilities import AssociationObject, Checks, PlayerObject, Vars
from Utilities.Analytics import stringify_gains
from Utilities.Combat import Belligerent, CombatEngine
from Utilities.ConfirmationMenu import ConfirmationMenu
from Utilities.Finances import Transaction
from Utilities.AyeshaBot import Ayesha

class Associations(commands.Cog):
    """Association Text"""

    def __init__(self, bot : Ayesha):
        self.bot = bot

        async def distribute_interest():
            psql1 = """
                    WITH valid_guild AS (
                        SELECT players.assc
                        FROM officeholders
                        INNER JOIN players
                            ON officeholders.officeholder = players.user_id
                        WHERE office = 'Comptroller'
                        ORDER BY id DESC
                        LIMIT 1
                    ),
                    comptroller_members AS (
                        SELECT user_id
                        FROM players
                        WHERE assc IN (SELECT * FROM valid_guild)
                    )
                    UPDATE guild_bank_account
                    SET account_funds = account_funds * 1.02 + 2500
                    WHERE user_id IN (SELECT * FROM comptroller_members);
                    """
            psql2 = """
                    WITH valid_guild AS (
                        SELECT players.assc
                        FROM officeholders
                        INNER JOIN players
                            ON officeholders.officeholder = players.user_id
                        WHERE office = 'Comptroller'
                        ORDER BY id DESC
                        LIMIT 1
                    ),
                    comptroller_members AS (
                        SELECT user_id
                        FROM players
                        WHERE assc IN (SELECT * FROM valid_guild)
                    )
                    UPDATE guild_bank_account
                    SET account_funds = account_funds * 1.01 + 1000
                    WHERE user_id NOT IN (SELECT * FROM comptroller_members);
                    """
            async with self.bot.db.acquire() as conn:
                await conn.execute(psql1)
                await conn.execute(psql2)

        def run_interest_func():
            asyncio.run_coroutine_threadsafe(
                distribute_interest(), self.bot.loop)

        async def schedule_interest_updates():
            interest_scheduler = schedule.Scheduler()
            interest_scheduler.every().saturday.at("06:00").do(run_interest_func)
            while True:
                interest_scheduler.run_pending()
                await asyncio.sleep(interest_scheduler.idle_seconds)

        asyncio.ensure_future(schedule_interest_updates())


    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Associations is ready.")

    a = discord.commands.SlashCommandGroup("association", 
        "Commands related to coop gameplay", )

    b = discord.commands.SlashCommandGroup("brotherhood",
        "Association commands exclusive to brotherhood members", 
        )

    c = discord.commands.SlashCommandGroup("college",
        "Association commands exclusive to college members", 
        )

    g = discord.commands.SlashCommandGroup("guild",
        "Association commands exclusive to guild members", 
        )

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
                    f"ATK, `{player.get_crit_rate()}` CRIT, `{player.get_hp()}` HP, "
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
                            f"`{champion.get_crit_rate()}`%\n"
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
        await paginator.respond(ctx.interaction)

    # COMMANDS
    @a.command()
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
                if assc.is_empty:
                    return await ctx.respond((
                        "You are not in an association. Use the "
                        "`/association join` command to join one!"))
            # Don't show disbanded guilds
            if assc.leader == 767234703161294858: # TODO: This is Ayesha's ID
                return await ctx.respond(
                    f"The {assc.type} with this name/ID has been disbanded.")

        await self.view_association(ctx, assc)

    @commands.user_command(name="View Association", 
        )
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

    @a.command()
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

    @a.command()
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

    @a.command()
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
            view = ConfirmationMenu(user=target)
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
            await msg.delete_original_response()
        
    @a.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_association)
    @cooldown(2, 86400, BucketType.user)
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

    @a.command()
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

    @a.command()
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

    @b.command()
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
            bonus_sources = [] # 2.0.3: for new stringify_gains()
            if player.occupation == "Engineer": # Occupation bonus
                bonus_sources.append((amount_stolen, "Engineer"))
                amount_stolen *= 2
            await player.give_gold(conn, amount_stolen)
            gold_gain_str = stringify_gains(
                "gold", amount_stolen, bonus_sources)
            await ctx.respond(
                f"You stole {gold_gain_str} from {victim.char_name}.")

    @b.command()
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
                return await ctx.respond(
                    f"Removed the champion in slot {slot}.")
            
            # Make sure player is in the brotherhood
            target = await PlayerObject.get_player_by_id(conn, champion.id)
            # if target.assc.id != player.assc.id:
            #     return await ctx.respond(
            #         "This player is not in your association.")
            # Otherwise sets the champion
            try:
                await assc.set_champion(conn, target.disc_id, slot)
            except Checks.PlayerAlreadyChampion:
                return await ctx.respond("This player is already a champion.")

            await ctx.respond(
                f"Added {target.char_name} to your the brotherhood's "
                f"roster of champions.")

    @b.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_assc_officer)
    async def attack(self, ctx):
        """Challenge another brotherhood to take over an outlying territory."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            attacker = player.assc

            # See if territory is available for attack. 1 attack per 3 hours
            psql = """
                    SELECT battle_date
                    FROM area_attacks
                    WHERE area = $1
                    ORDER BY id DESC
                    LIMIT 1;
                    """
            last_battle = await conn.fetchval(psql, attacker.base)
            if last_battle is not None:
                time_diff = datetime.now() - last_battle
                if time_diff.total_seconds() < 10800:
                    time_left = 10800 - time_diff.total_seconds()
                    fseconds = time.gmtime(time_left)
                    return await ctx.respond(
                        f"**{attacker.base}** has already suffered a recent "
                        f"attack. Please try again in "
                        f"`{time.strftime('%H:%M:%S', fseconds)}`.")

            # Load defender and see if attack can be ended prematurely
            defender = await AssociationObject.get_territory_controller(
                conn, attacker.base)
            if defender.is_empty: # Unowned, give to attacker peacefully
                await attacker.set_territory_controller(conn, attacker.base)
                await self.bot.announcement_channel.send(
                    f"**{attacker.name}** (ID: `{attacker.id}`) has seized "
                    f"control over **{attacker.base}**.")
                return await ctx.respond(
                    f"Your guild successfully occupied **{attacker.base}**.")
            elif attacker.id == defender.id:
                return await ctx.respond(
                    f"Your brotherhood is already in control of "
                    f"**{attacker.base}**!")

            # Load champions from brotherhoods
            att_team = await attacker.get_champions(conn)
            def_team = await defender.get_champions(conn)

            # Check for valid fighters or premature victory
            if att_team == [None]*len(att_team): # See if its no champs
                return await ctx.respond(
                    "Your brotherhood has no champions. Set some using "
                    "`/brotherhood champion`.")
                
            if def_team == [None]*len(def_team):
                # If defender has no champions, give it away
                await attacker.set_territory_controller(conn, attacker.base)
                await self.bot.announcement_channel.send(
                    f"**{attacker.name}** (ID: `{attacker.id}`) has defeated "
                    f"**{defender.name}** (ID: `{defender.id}`) and seized "
                    f"control over **{attacker.base}**!")
                return await ctx.respond(
                    f"Your guild successfully occupied **{attacker.base}**.")

        # Sort and fill teams, checking for repeats
        for team in (att_team, def_team):
            empties = team.count(None)
            for _ in range(empties):
                team.remove(None)
                team.append(team[0])

        # Change to Belligerents for easier stat changes
        for i in range(len(att_team)):
            att_team[i] = Belligerent.CombatPlayer(att_team[i])
            def_team[i] = Belligerent.CombatPlayer(def_team[i])

        # Nerf repeat characters
        for team in (att_team, def_team):
            for i in range(1,len(team)):
                if team[i].disc_id == team[i-1].disc_id:
                    team[i].attack = int(team[i].attack * .75)
                    team[i].current_hp = int(team[i].current_hp * .75)
                if i == 2 and team[i].disc_id == team[i-2].disc_id:
                    team[i].attack = int(team[i].attack * .75)
                    team[i].current_hp = int(team[i].current_hp * .75)

        # Conduct PvP operations between champions
        attacker_wins = 0
        defender_wins = 0
        battle_results = []

        for i in range(len(att_team)): # Always 3
            engine, results = CombatEngine.CombatEngine.initialize(
                att_team[i], def_team[i], 15
            )
            battle_log = []
            while engine:
                battle_log.append(results.description)
                actor = engine.actor
                action = engine.recommend_action(actor, results)
                engine.process_turn(action)
            battle_log.append(results.description)
            
            if engine.get_victor() == att_team[i]:
                attacker_wins += 1
            else:
                defender_wins += 1

            # With battle over, create embed displaying results
            embed = discord.Embed(
                title=f"Battle for {attacker.base}: {i+1}",
                color=Vars.ABLUE)
            embed.add_field(
                name=att_team[i].name,
                value=(
                    f"ATK: `{att_team[i].attack}` | CRIT: `{att_team[i].crit_rate}%`"
                    f"\nHP: `{att_team[i].current_hp}` | DEF: "
                    f"`{att_team[i].defense}%`"))  
            embed.add_field(
                name=def_team[i].name,
                value=(
                    f"ATK: `{def_team[i].attack}` | CRIT: `{def_team[i].crit_rate}%`"
                    f"\nHP: `{def_team[i].current_hp}` | DEF: "
                    f"`{def_team[i].defense}%`"))
            embed.add_field(
                name="Battle Log", 
                value="\n\n".join(battle_log[-3:]),
                inline=False)
            battle_results.append(embed)

        # Log battle and change controller
        if attacker_wins > defender_wins:
            embed = discord.Embed(
                title=
                    f"{attacker.name} has seized control over {attacker.base}!",
                description=(
                    f"**{attacker.name}** have bested **{defender.name}** "
                    f"in a trial of combat, becoming the prominent gang of "
                    f"the region.\n"
                    f"View the following pages to see the results of the "
                    f"battles between both brotherhood's champions."),
                color=Vars.ABLUE)
            async with self.bot.db.acquire() as conn:
                await attacker.set_territory_controller(conn, attacker.base)
            winner = attacker.id

        else:
            embed = discord.Embed(
                title=
                    f"{defender.name} retains control over {attacker.base}!",
                description=(
                    f"**{defender.name}** have bested **{attacker.name}** "
                    f"in a trial of combat, protecting their status as the "
                    f"prominent gang of the region.\n"
                    f"View the following pages to see the results of the "
                    f"battles between both brotherhood's champions."),
                color=Vars.ABLUE)
            winner = defender.id

        async with self.bot.db.acquire() as conn: # 3 times; improve this
            await AssociationObject.log_area_attack(
                conn, attacker.base, attacker.id, defender.id, winner)

        embed.set_image(url="https://i.imgur.com/jpLztYK.jpg")
        battle_results.insert(0, embed)

        # Output pages
        paginator = pages.Paginator(pages=battle_results, timeout=30)
        await paginator.respond(ctx.interaction)

    # --------------------------------------
    # ----- COLLEGE EXCLUSIVE COMMANDS -----
    # --------------------------------------

    @c.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_college)
    @cooldown(1, 14400, BucketType.user)
    async def usurp(self, ctx):
        """Make a political play for power, gaining a few gravitas."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            chance = random.randint(1,4)
            gravitas = 0
            gravitas_bonus_sources = []
            if player.occupation == "Engineer":
                gravitas = 5
                gravitas_bonus_sources.append((5, "Engineer"))
            gravitas += player.assc.get_level()
            gravitas_bonus_sources.append(
                (player.assc.get_level(), "College Level"))

            if chance == 1: # Failure
                gravitas -= random.randint(16, 25)
                gravitas_gain_str = stringify_gains(
                    "gravitas", gravitas*-1, gravitas_bonus_sources)
                message = (
                    f"Your political play was wildly unpopular with the "
                    f"people of {player.location}. You lost "
                    f"{gravitas_gain_str}.")
            elif chance == 2: # Big success
                gravitas += random.randint(12, 25)
                gravitas_gain_str = stringify_gains(
                    "gravitas", gravitas, gravitas_bonus_sources)
                message = (
                    f"Your maneuver was received with raucous applause from "
                    f"the people of {player.location}. You gained "
                    f"{gravitas_gain_str}.")
            else:
                gravitas += random.randint(3, 10)
                gravitas_gain_str = stringify_gains(
                    "gravitas", gravitas, gravitas_bonus_sources)
                message = (
                    f"Your speech turned some heads but most of the people of "
                    f"{player.location} are apathetic to your rhetoric. You "
                    f"gained {gravitas_gain_str}.")
            
            await player.give_gravitas(conn, gravitas)
            await ctx.respond(message)



    # ------------------------------------
    # ----- GUILD EXCLUSIVE COMMANDS -----
    # ------------------------------------

    @g.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @cooldown(1, 7200, BucketType.user)
    async def invest(self, ctx, capital : Option(int,
            description="The amount of money you are investing, up to 250000",
            min_value=100,
            max_value=250000)):
        """Invest in a nearby project and gain/lose some money."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.gold < capital:
                raise Checks.NotEnoughGold(capital, player.gold)
            
            # Determine the return
            bonus_occ = player.occupation == "Engineer"
            gold_bonus_sources = []
            multiplier = random.randint(0, 21500) / 10000.0 # up to 2.15x
            return_amt = int(capital * multiplier) 
            if bonus_occ:
                gold_bonus_sources.append((return_amt // 4), "Engineer")
                return_amt += return_amt // 4

            # Pick random things to display to player
            projects = ("museum", "church", "residence", 
                "fishing company", "game company", "guild", "boat", 
                "road construction", "cooperative", "ponzi scheme", "MLM",
                "non-fungible token", "animal herd", "mercenary band")
            project = random.choice(projects)

            # Determine if loss or gain
            capital_gains = return_amt - capital
            gold_gains_str = stringify_gains(
                "gold", capital_gains, gold_bonus_sources)
            if capital_gains > 0: # Player made money, tax it
                sale = await Transaction.create_sale(
                    conn, player, capital_gains)
                print_tax = await sale.log_transaction(conn, "sale")

                message = (
                    f"You invested `{capital}` gold in a {project} and made a "
                    f"return of {gold_gains_str}. {print_tax}")
            else:
                await player.give_gold(conn, capital_gains)
                message = (
                    f"You invested `{capital}` gold in a {project} and made a "
                    f"return of {gold_gains_str}. Since you lost money, you "
                    f"were not taxed.")
            await ctx.respond(message)

    @g.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    async def account(self, ctx, 
            action : Option(str,
                description="What you are doing with your bank account",
                choices=[OptionChoice(name=t) for t in 
                    ("View Bank Account", "Deposit Gold", "Withdraw Gold")]),
            transaction : Option(int,
                description="The gold you are depositing/withdrawing, if any",
                required=False,
                min_value=1)):
        """Safely store gold in your guild bank account"""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            # First loads the bank account and creates one if it does not exist
            # Also returns the current funds
            # If there is a conflict the INSERT won't return anything so the
            # second UNION will get it. If the INSERT does return something,
            # both values (should be) the same so no harm done
            psql = """
                    WITH insertion AS (
                        INSERT INTO guild_bank_account (user_id)
                        VALUES ($1)
                        ON CONFLICT (user_id) DO NOTHING
                        RETURNING account_funds
                    )
                    SELECT account_funds 
                    FROM insertion
                    UNION
                        SELECT account_funds
                        FROM guild_bank_account
                        WHERE user_id = $1;
                    """
            funds = await conn.fetchval(psql, player.disc_id)

            if action == "View Bank Account":
                return await ctx.respond(
                    f"You have `{funds}` gold in your guild bank account.")
            elif transaction is None:
                return await ctx.respond((
                    "Please include the amount of gold you are depositing "
                    "or withdrawing."))

            # Condition above handles missing transaction parameter
            if action == "Deposit Gold":
                # Make sure they have the gold they are trying to deposit
                if transaction > player.gold:
                    raise Checks.NotEnoughGold(transaction, player.gold)
                await player.give_gold(conn, transaction*-1)
            else:
                if transaction > funds:
                    return await ctx.respond((
                        f"You cannot withdraw that amount as you only have "
                        f"`{funds}` gold in your bank account."))
                await player.give_gold(conn, transaction)
                transaction *= -1

            psql = """
                    UPDATE guild_bank_account
                    SET account_funds = account_funds + $1
                    WHERE user_id = $2;
                    """
            await conn.execute(psql, transaction, player.disc_id)
            await ctx.respond((
                f"Your transaction was a success! You now have `{player.gold}` "
                f"gold on-hand, and `{funds+transaction}` remaining in your "
                f"account."))


def setup(bot):
    bot.add_cog(Associations(bot))