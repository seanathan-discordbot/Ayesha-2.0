import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

import asyncio
from discord.ext.commands.flags import F
import schedule
import time

from Utilities import Checks, CombatObject, PlayerObject, Vars
from Utilities.CombatObject import CombatInstance
from Utilities.ConfirmationMenu import OfferMenu

class Misc(commands.Cog):
    """Non-gameplay related commands"""

    def __init__(self, bot):
        self.bot = bot
        self.daily_scheduler = schedule.Scheduler()

        def clear_dailies():
            self.bot.recent_voters.clear()

        async def update_dailies():
            self.daily_scheduler.every().day.at("00:00").do(clear_dailies)
            while True:
                self.daily_scheduler.run_pending()
                await asyncio.sleep(self.daily_scheduler.idle_seconds)

        asyncio.ensure_future(update_dailies())

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Misc is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def daily(self, ctx):
        """Get 2 rubidics daily. Resets everyday at 12 a.m. EST."""
        if ctx.author.id not in self.bot.recent_voters:
            self.bot.recent_voters[ctx.author.id] = 0
            # async with self.bot.db.acquire() as conn:
            #     player = await PlayerObject.get_player_by_id(
            #         conn, ctx.author.id)
            #     await player.give_rubidics(conn, 2)
            title = "You claimed 2 Rubidics from your daily!"
        else:
            title = "You already claimed your daily today."

        left_to_refresh = time.gmtime(self.daily_scheduler.idle_seconds)
        embed = discord.Embed(
            title=title,
            description=(
                f"You can claim your daily again in "
                f"`{time.strftime('%H:%M:%S', left_to_refresh)}`."),
            color=Vars.ABLUE
        )
        embed.add_field(
            name="Vote for the bot on top.gg to receive an additional rubidic!",
            value=(
                "[**CLICK HERE**](https://top.gg/bot/767234703161294858) "
                "to vote for the bot for rubidics!\n\n"
                "Any questions? Join the "
                "[**support server**](https://discord.gg/FRTTARhN44)!"))
        embed.set_thumbnail(url="https://i.imgur.com/LPxc3zI.jpeg")

        await ctx.respond(embed=embed)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def cooldowns(self, ctx):
        """View any of your active cooldowns."""
        # Iterate through commands to get cooldowns
        cooldowns = []

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

        # Get player's adventure status
        if player.destination == "EXPEDITION":
            elapsed = int(time.time() - player.adventure)
            subday = elapsed % 86400
            subday_str = time.strftime("%H:%M:%S", time.gmtime(subday))
            days = str(int(elapsed / 86400))
            days = "0"+days if len(days) == 1 else days
            adv_status = (
                f"You have been on an expedition for `{days}:{subday_str}`."
            )
        elif player.adventure is None:
            adv_status = "You are not currently on an adventure."
        elif player.adventure > int(time.time()): # TRAVEL not done
            time_left = player.adventure - int(time.time())
            str_time = time.strftime('%H:%M:%S', time.gmtime(time_left))
            adv_status = (
                f"You will arrive at **{player.destination}** in "
                f"`{str_time}`.")
        else:
            adv_status = (
                f"Your adventure is completed and you can safely `/arrive` "
                f"at **{player.destination}**.")

        # Check if player has claiemd daily today
        if ctx.author.id in self.bot.recent_voters:
            to_reset = time.gmtime(self.daily_scheduler.idle_seconds)
            daily = (
                f"You can claim your daily again in "
                f"`{time.strftime('%H:%M:%S', to_reset)}`")
        else:
            daily = (
                "You can claim your free daily 2 rubidics with the `/daily` "
                "command.")

        # Create an embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Cooldowns",
            description="\n".join(cooldowns),
            color=Vars.ABLUE)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.add_field(
            name="Adventure Status",
            value=adv_status)
        embed.add_field(
            name="Daily Status",
            value=daily,
            inline=False)

        await ctx.respond(embed=embed)
        

def setup(bot):
    bot.add_cog(Misc(bot))