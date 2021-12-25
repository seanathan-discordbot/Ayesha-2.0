from os import name
import discord
from discord.commands.commands import Option, SlashCommand

from discord.ext import commands

from Utilities import Checks, Vars, PlayerObject, Analytics

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

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Profile is ready.")

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
            await PlayerObject.create_character(
                await self.bot.db.acquire(),
                ctx.author.id,
                name
            )
            await ctx.respond(f"Started the game: {name}")
        else:
            await ctx.respond(f"You cancelled :(")
        await msg.delete_original_message()

    @commands.slash_command(guild_ids=[762118688567984151])
    async def profile(self, ctx, 
            player : Option(commands.UserConverter,
                description="the person whose profile you want to see",
                required=False, default=None)):
        """View yours or any other player's profile"""
        if player is None: # return author profile
            player = ctx.author
        
        profile = await PlayerObject.get_player_by_id(
            await self.bot.db.acquire(),
            player.id)

        xp_rank = await Analytics.get_xp_rank(
            await self.bot.db.acquire(), player.id)
        go_rank = await Analytics.get_gold_rank(
            await self.bot.db.acquire(), player.id)
        gr_rank = await Analytics.get_gravitas_rank(
            await self.bot.db.acquire(), player.id)
        bw_rank = await Analytics.get_bosswins_rank(
            await self.bot.db.acquire(), player.id)
        pw_rank = await Analytics.get_pvpwins_rank(
            await self.bot.db.acquire(), player.id)

        embed = discord.Embed(
            title=f"{player.display_name}'s Profile: {profile.char_name}",
            color=Vars.ABLUE)
        embed.set_thumbnail(url=player.avatar.url)
        embed.add_field(
            name="Character Info",
            value=(
                f"Gold: `{profile.gold}`\nOccupation: `{profile.occupation}`"
                f"\nOrigin: `{profile.origin}`\nLocation: `{profile.location}`"
                f"\nAssociation: `{profile.assc.name} (ID: {profile.assc.id})` "
            ),
            inline=True)
        embed.add_field(
            name="Character Stats",
            value=(
                f"Level: `{profile.level}`\nGravitas: `{profile.gravitas}`\n"
                f"Attack: `{profile.get_attack()}`\nCrit: "
                f"`{profile.get_crit()}%`\nHP: `{profile.get_hp()}`\n"),
            inline=True)
        embed.add_field(
            name="Party",
            value=(
                f"Item: `{profile.equipped_item.name} "
                f"({profile.equipped_item.rarity})`\nAcolyte: "
                f"`{profile.acolyte1.acolyte_name} ("
                f"{profile.acolyte1.gen_dict['Rarity']}⭐)`\nAcolyte: "
                f"`{profile.acolyte2.acolyte_name} ("
                f"{profile.acolyte2.gen_dict['Rarity']}⭐)`"),
                inline=True)
        embed.add_field(
            name="Ranks",
            value=(
                f"You are:\n"
                f"`{xp_rank}` in most xp.\n"
                f"`{go_rank}` in wealthiest players.\n"
                f"`{gr_rank}` in most influential players.\n"
                f"`{bw_rank}` in having the most PvE wins.\n"
                f"`{pw_rank}` in having the most PvP wins."
            ),
            inline=False
        )
        embed.set_footer(text=f"Profile for user {player.id}")

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Profile(bot))