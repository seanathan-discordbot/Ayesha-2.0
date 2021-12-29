import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import converter

import asyncio
import schedule

from Utilities import Checks, ItemObject, Vars, Analytics, PlayerObject

class ConfirmButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10.0)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.grey)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        self.stop()

class Profile(commands.Cog):
    """Create a character and view your stats!"""

    def __init__(self, bot):
        self.bot = bot

        async def update_gravitas():
            # Decay all player's gravitas
            # Formula: https://i.imgur.com/jMFS3Ch.png
            psql1 = """
                    UPDATE players
                    SET gravitas = gravitas - (gravitas / 5)
                    WHERE gravitas < 500
                        AND loc NOT IN ('Aramithea', 'Riverburn', 'Thenuille');
                    """
            psql2 = """
                    UPDATE players
                    SET gravitas = gravitas + 100 - (2 * gravitas / 5)
                    WHERE gravitas >= 500 AND gravitas < 1000
                        AND loc NOT IN ('Aramithea', 'Riverburn', 'Thenuille');
                    """
            psql3 = """
                    UPDATE players
                    SET gravitas = gravitas + 500 - (4 * gravitas / 5)
                    WHERE gravitas >= 1000
                        AND loc NOT IN ('Aramithea', 'Riverburn', 'Thenuille');
                    """
            psql4 = """
                    UPDATE players
                    SET gravitas = gravitas - (gravitas / 10)
                    WHERE gravitas < 500
                        AND loc IN ('Aramithea', 'Riverburn', 'Thenuille');
                    """
            psql5 = """
                    UPDATE players
                    SET gravitas = gravitas + 50 - (gravitas / 5)
                    WHERE gravitas >= 500 AND gravitas < 1000
                        AND loc IN ('Aramithea', 'Riverburn', 'Thenuille');
                    """
            psql6 = """
                    UPDATE players
                    SET gravitas = gravitas + 650 - (4 * gravitas / 5)
                    WHERE gravitas >= 1000
                        AND loc IN ('Aramithea', 'Riverburn', 'Thenuille');
                    """
            # APPLY GRAVITAS PASSIVE INCOME
            # Class Bonuses: Farmer 4; Soldier, Scribe 1
            psql7 = """
                    UPDATE players 
                    SET gravitas = gravitas + 4
                    WHERE occupation = 'Farmer';
                    """
            psql8 = """
                    UPDATE players
                    SET gravitas = gravitas + 1
                    WHERE occupation IN ('Soldier', 'Scribe');
                    """
            # Origin Bonuses: Aramithea 5, Cities 3, Some 1
            psql9 = """
                    UPDATE players
                    SET gravitas = gravitas + 5
                    WHERE origin = 'Aramithea';
                    """
            psqla = """
                    UPDATE players
                    SET gravitas = gravitas + 3
                    WHERE origin IN ('Riverburn', 'Thenuille');
                    """
            psqlb = """
                    UPDATE players
                    SET gravitas = gravitas + 1
                    WHERE origin IN ('Mythic Forest', 'Lunaris', 'Crumidia');
                    """
            # College Members get 7
            psqlc = """
                    WITH colleges AS (
                        SELECT DISTINCT players.assc
                        FROM players
                        INNER JOIN associations
                            ON players.assc = associations.assc_id
                        WHERE associations.assc_type = 'College'
                    )
                    UPDATE players
                    SET gravitas = gravitas + 7
                    WHERE assc IN (SELECT assc FROM colleges);
                    """
            # Acolyte Bonuses: Ajar, Duchess 2
            psqld = """
                    WITH ajar_users AS (
                        WITH acolyte1 AS (
                            SELECT players.user_id
                            FROM players
                            INNER JOIN acolytes
                                ON players.acolyte1 = acolytes.acolyte_id
                            WHERE acolytes.acolyte_name = 'Ajar'
                        ),
                        acolyte2 AS (
                            SELECT players.user_id
                            FROM players
                            INNER JOIN acolytes
                                ON players.acolyte2 = acolytes.acolyte_id
                            WHERE acolytes.acolyte_name = 'Ajar'
                        )
                        SELECT * FROM acolyte1
                        UNION
                        SELECT * FROM acolyte2
                    )
                    UPDATE players
                    SET gravitas = gravitas + 2
                    WHERE user_id IN (SELECT user_id FROM ajar_users);
                    """
            psqle = """
                    WITH duchess_users AS (
                        WITH acolyte1 AS (
                            SELECT players.user_id
                            FROM players
                            INNER JOIN acolytes
                                ON players.acolyte1 = acolytes.acolyte_id
                            WHERE acolytes.acolyte_name = 'Duchess'
                        ),
                        acolyte2 AS (
                            SELECT players.user_id
                            FROM players
                            INNER JOIN acolytes
                                ON players.acolyte2 = acolytes.acolyte_id
                            WHERE acolytes.acolyte_name = 'Duchess'
                        )
                        SELECT * FROM acolyte1
                        UNION
                        SELECT * FROM acolyte2
                    )
                    UPDATE players
                    SET gravitas = gravitas + 2
                    WHERE user_id IN (SELECT user_id FROM duchess_users);
                    """
            async with self.bot.db.acquire() as conn:
                await conn.execute(psql1)
                await conn.execute(psql2)
                await conn.execute(psql3)
                await conn.execute(psql4)
                await conn.execute(psql5)
                await conn.execute(psql6)
                await conn.execute(psql7)
                await conn.execute(psql8)
                await conn.execute(psql9)
                await conn.execute(psqla)
                await conn.execute(psqlb)
                await conn.execute(psqlc)
                await conn.execute(psqld)
                await conn.execute(psqle)

        def run_gravitas_func():
            asyncio.run_coroutine_threadsafe(update_gravitas(), self.bot.loop)

        async def schedule_gravitas_updates():
            gravitas_scheduler = schedule.Scheduler()
            gravitas_scheduler.every().day.at("12:00").do(run_gravitas_func)
            while True:
                gravitas_scheduler.run_pending()
                await asyncio.sleep(gravitas_scheduler.idle_seconds)

        asyncio.ensure_future(schedule_gravitas_updates())


    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Profile is ready.")

    # AUXILIARY METHODS
    async def view_profile(self, ctx, player : discord.Member):
        """Loads and prints the player's profile."""
        await ctx.defer()

        async with self.bot.db.acquire() as conn:
            # Load information
            print("Loading profile.")
            profile = await PlayerObject.get_player_by_id(conn, player.id)
            print("Calculating level")
            level, dist = profile.get_level(get_next=True)
            print("Getting resources")
            pack = await profile.get_backpack(conn)
            print("Getting ranks")
            gold_rank = Analytics.stringify_rank(
                await Analytics.get_gold_rank(conn, player.id))
            gravitas_rank = Analytics.stringify_rank(
                await Analytics.get_gravitas_rank(conn, player.id))
            xp_rank = Analytics.stringify_rank(
                await Analytics.get_xp_rank(conn, player.id))
            pve_rank = Analytics.stringify_rank(
                await Analytics.get_bosswins_rank(conn, player.id))
            pvp_rank = Analytics.stringify_rank(
                await Analytics.get_pvpwins_rank(conn, player.id))
            
            # Create pages
            print("Creating embeds")
            page1 = discord.Embed(            
                title=f"Character Information: {profile.char_name}",
                color=Vars.ABLUE
            )
            page1.set_thumbnail(url=player.avatar.url)
            page1.add_field(name="Experience",
                value=(
                    f"Level: `{level}`\n"
                    f"EXP: `{profile.xp}` (`{xp_rank}`)\n"
                    f"To Next Level: `{dist}`"),
                inline=True)
            page1.add_field(name="Wealth",
                value=(
                    f"Gold: `{profile.gold}` (`{gold_rank}`)\n"
                    f"Gravitas: `{profile.gravitas}` (`{gravitas_rank}`)"),
                inline=True)
            page1.add_field(name="Lore",
                value=(
                    f"Occupation: `{profile.occupation}`\n"
                    f"Origin: `{profile.origin}`\n"
                    f"Location: `{profile.location}`\n"
                    f"Association: `{profile.assc.name}` "
                    f"(ID: `{profile.assc.id}`)"),
                inline=False)

            page2 = discord.Embed(            
                title=f"Combat Loadout: {profile.char_name}",
                color=Vars.ABLUE
            )
            page2.set_thumbnail(url=player.avatar.url)
            page2.add_field(name="General",
                value=(
                    f"Attack: `{profile.get_attack()}`\n"
                    f"Crit Chance: `{profile.get_crit()}%`\n"
                    f"Hit Points: `{profile.get_hp()}`\n"
                    f"Defense: `{profile.get_defense()}%`"),
                inline=True)
            page2.add_field(name="Reputation",
                value=(
                    f"Bosses Defeated: `{profile.boss_wins}` (`{pve_rank}`)\n"
                    f"Pvp Wins: `{profile.pvp_wins}` (`{pvp_rank}`)\n"),
                inline=True)
            page2.add_field(name=f"Equips",
                value=(
                    f"{profile.equipped_item.type}: {profile.equipped_item.name} "
                    f"({profile.equipped_item.rarity}, `"
                    f"{profile.equipped_item.attack}` ATK, `"
                    f"{profile.equipped_item.crit}` CRIT)"
                    f"\n"
                    f"{profile.helmet.name} (`{profile.helmet.defense}` DEF)"
                    f"\n"
                    f"{profile.bodypiece.name} (`{profile.bodypiece.defense}` "
                    f"DEF)"
                    f"\n"
                    f"{profile.boots.name} (`{profile.boots.defense}` DEF)"
                    f"\n"
                    f"Accessory: {profile.accessory.name}"
                ),
                inline=False)
            page2.add_field(name="Acolyte",
                value=(
                    f"{profile.acolyte1.acolyte_name} (`"
                    f"{profile.acolyte1.gen_dict['Rarity']}⭐`)"
                ),
                inline=True)
            page2.add_field(name="Acolyte",
                value=(
                    f"{profile.acolyte2.acolyte_name} (`"
                    f"{profile.acolyte2.gen_dict['Rarity']}⭐`)"
                ),
                inline=True)

            page3 = discord.Embed(            
                title=f"Backpack: {profile.char_name}",
                color=Vars.ABLUE
            )
            page3.set_thumbnail(url=player.avatar.url)
            for resource in Vars.MATERIALS:
                page3.add_field(name=resource, value=pack[resource.lower()])

            if profile.assc.is_empty:
                embeds = [page1, page2, page3]
            else:
                # Print the player association as the last page
                assc_leader = await ctx.bot.fetch_user(profile.assc.leader)
                assc_members = await profile.assc.get_member_count(conn)
                assc_capacity = profile.assc.get_member_capacity()
                assc_level, progress = profile.assc.get_level(give_graphic=True)

                page4 = discord.Embed(            
                    title=f"{profile.assc.type}: {profile.assc.name}",
                    color=Vars.ABLUE
                )
                page4.set_thumbnail(url=profile.assc.icon)
                page4.add_field(name="Leader", value=assc_leader.mention)
                page4.add_field(name="Members", 
                    value=f"{assc_members}/{assc_capacity}")
                page4.add_field(name="Level", value=assc_level)
                page4.add_field(name="EXP Progress", value=progress)
                page4.add_field(name="Base", value=profile.assc.base)
                if profile.assc.join_status != "open":
                    page4.add_field(name=
                        f"This {profile.assc.type} is closed to new members.",
                        value=profile.assc.desc,
                        inline=False)
                else:
                    page4.add_field(name=(
                        f"This {profile.assc.type} is open to new members at or "
                        f"above level {profile.assc.lvl_req}."),
                        value=profile.assc.desc,
                        inline=False)
                page4.set_footer(text=f"{profile.assc.type} ID: {profile.assc.id}")
                embeds = [page1, page2, page3, page4]

        # Output pages
        print("Paginating")
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
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.not_player)
    async def start(self, ctx, 
            name: Option(str, description="Your character's name",
                required=False, default=None)):
        """Start the game of Ayesha."""
        if not name:
            name = ctx.author.name
        if len(name) > 32:
            raise Checks.ExcessiveCharacterCount(limit=32)

        embed = discord.Embed(
            title="Start the game of Ayesha?",
            color=Vars.ABLUE)
        embed.add_field(
            name=f"Your Name: {name}",
            value=(f"You can customize your name by redoing this command with "
                   f"the `name` parameter filled!"))
        view = ConfirmButton()
        msg = await ctx.respond(embed=embed, view=view)
        await view.wait()
        if view.value is None:
            await ctx.respond("Timed out.")
        elif view.value:
            async with self.bot.db.acquire() as conn:
                await PlayerObject.create_character(conn, ctx.author.id, name)
                await ctx.respond(f"Started the game: {name}")
        else:
            await ctx.respond(f"You cancelled :(")
        await msg.delete_original_message()

    @commands.slash_command(name="profile", guild_ids=[762118688567984151])
    async def self_profile(self, ctx, player : Option(discord.Member,
                description="Another player whose profile you want to see",
                required=False,
                converter=commands.MemberConverter())):
        """View your profile."""
        if player is not None:
            await self.view_profile(ctx, player)
        else:
            await self.view_profile(ctx, ctx.author)

    @commands.user_command(name="View Profile", guild_ids=[762118688567984151])
    async def other_profile(self, ctx, member: discord.Member):
        await self.view_profile(ctx, member)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def rename(self, ctx, *, 
            target : Option(str,
                description="Rename either your character or weapon",
                choices=[
                    OptionChoice(name="Rename Character"),
                    OptionChoice(name="Rename Weapon")],
                default=""),
            name : Option(str, description="The new name.", required=True),
            weapon : Option(int, 
                description="Put the ID of the weapon you are renaming",
                required=False)):
        """Change your character's or weapon's name."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if target == "Rename Character":
                await player.set_char_name(conn, name)
                await ctx.respond(f"You changed your name to **{name}**.")
            else:
                if weapon is None:
                    return await ctx.respond(
                        "You didn't supply a weapon ID to rename!")
                if not await player.is_weapon_owner(conn, weapon):
                    raise Checks.NotWeaponOwner
                item = await ItemObject.get_weapon_by_id(conn, weapon)
                old_name = item.name
                await item.set_name(conn, name)
                await ctx.respond((
                    f"You renamed `{item.weapon_id}`: {old_name} to "
                    f"{item.name}."))

    # TODO: Add tutorial; this should probably go last



def setup(bot):
    bot.add_cog(Profile(bot))