import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages

import asyncio

from Utilities import Checks, ItemObject, Vars, Analytics, PlayerObject
from Utilities.AyeshaBot import Ayesha
from Utilities.ConfirmationMenu import ConfirmationMenu

class Profile(commands.Cog):
    """Create a character and view your stats!"""

    def __init__(self, bot : Ayesha):
        self.bot = bot

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
            profile = await PlayerObject.get_player_by_id(conn, player.id)
            level, dist = profile.get_level(get_next=True)
            pack = await profile.get_backpack(conn)
            gold_rank = Analytics.stringify_rank(
                await Analytics.get_gold_rank(conn, player.id))
            gravitas_rank = Analytics.stringify_rank(
                await Analytics.get_gravitas_rank(conn, player.id))
            xp_rank = Analytics.stringify_rank(
                await Analytics.get_xp_rank(conn, player.id))
            pve_rank = Analytics.stringify_rank(
                await Analytics.get_bosswins_rank(conn, player.id))
            pvelvl_rank = Analytics.stringify_rank(
                await Analytics.get_boss_level_rank(conn, player.id)
            )
            pvp_rank = Analytics.stringify_rank(
                await Analytics.get_pvpwins_rank(conn, player.id))
            
            # Create pages
            page1 = discord.Embed(            
                title=f"Character Information: {profile.char_name}",
                color=Vars.ABLUE
            )
            page1.set_thumbnail(url=player.display_avatar.url)
            page1.add_field(name="Experience",
                value=(
                    f"Level: `{level}`\n"
                    f"EXP: `{profile.xp}` (`{xp_rank}`)\n"
                    f"To Next Level: `{dist}`"),
                inline=True)
            page1.add_field(name="Wealth",
                value=(
                    f"Gold: `{profile.gold}` (`{gold_rank}`)\n"
                    f"Gravitas: `{profile.gravitas}` (`{gravitas_rank}`)\n"
                    f"Rubidics: `{profile.rubidics}`"),
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
            page2.set_thumbnail(url=player.display_avatar.url)
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
                    f"Highest Level Reached: `{profile.pve_limit}` "
                    f"(`{pvelvl_rank}`)\n"
                    f"Pvp Wins: `{profile.pvp_wins}` (`{pvp_rank}`)\n"),
                inline=True)
            page2.add_field(name=f"Equips",
                value=(
                    f"{profile.equipped_item.type}: {profile.equipped_item.name} "
                    f"(`{profile.equipped_item.attack}` ATK, "
                    f"`{profile.equipped_item.crit}` CRIT)"
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
                value=f"({profile.acolyte1.stars}) {profile.acolyte1.name}",
                inline=True)
            page2.add_field(name="Acolyte",
                value=f"({profile.acolyte2.stars}) {profile.acolyte2.name}",
                inline=True)

            page3 = discord.Embed(            
                title=f"Backpack: {profile.char_name}",
                color=Vars.ABLUE
            )
            page3.set_thumbnail(url=player.display_avatar.url)
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
        paginator = pages.Paginator(pages=embeds, timeout=30)
        await paginator.respond(ctx.interaction)

    # COMMANDS
    @commands.slash_command()
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
        view = ConfirmationMenu(user=ctx.author, timeout=30.0)
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

    @commands.slash_command(name="profile", )
    async def self_profile(self, ctx, player : Option(discord.Member,
                description="Another player whose profile you want to see",
                required=False,
                converter=commands.MemberConverter())):
        """View your profile."""
        if player is not None:
            await self.view_profile(ctx, player)
        else:
            await self.view_profile(ctx, ctx.author)

    @commands.user_command(name="View Profile", )
    async def other_profile(self, ctx, member: discord.Member):
        await self.view_profile(ctx, member)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def rename(self, ctx, 
            target : Option(str,
                description="Rename either your character or weapon",
                choices=[
                    OptionChoice(name="Rename Character"),
                    OptionChoice(name="Rename Weapon")],
                required=True),
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
                    

def setup(bot):
    bot.add_cog(Profile(bot))