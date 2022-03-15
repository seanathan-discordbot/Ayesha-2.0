import discord
from discord import Option

from discord.ext import commands, tasks

import asyncio
import time
from datetime import timedelta


class Reminders(commands.Cog):
    """Reminders text"""

    def __init__(self,bot):
        self.bot = bot

    @tasks.loop(seconds=15.0)
    async def check_for_reminders(self):
        now = int(time.time())
        # Function to get all reminders
    
    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Reminders is ready.")

    def cog_unload(self):
        self.check_for_reminders.stop()
        return super().cog_unload()

    # COMMANDS
    r = discord.commands.SlashCommandGroup("remind", 
        "Set reminders for Ayesha gameplay",
        guild_ids=[762118688567984151])

    @r.command(guild_ids=[762118688567984151])
    async def create(self, ctx : discord.ApplicationContext, 
            duration : Option(str,
                description="Time until reminder: Use DD:HH:MM:SS or MM:SS format",
                required=True), 
            content : Option(
                str,
                description="What you want to be reminded of",
                required=True)):
        """Set a reminder for yourself."""
        # Parse the input
        if len(content) > 255:
            return await ctx.respond(
                f"Please limit your reminder to 255 characters. Yours is "
                f"`{len(content)}`.")

        length = 0

        timer = [s.strip() for s in duration.split(':')]
        for t in timer:
            if not t.isdigit(): # Invalid input
                return await ctx.respond(
                    "Please follow the format `days:hours:minutes:seconds`.")

        # This converts everything to seconds
        # Appears confusing, goes backwards from the list and multiplies it
        # by the unit-conversion
        conv = {
            1 : 1, # seconds to seconds
            2 : 60, # minutes to seconds
            3 : 3600, # hours to seconds
            4: 86400, # days to seconds
        }
        for i in range(1, len(timer)+1):
            length += int(timer[-i]) * conv[i]
        
        SECONDS_IN_YEAR = 31536000
        if length > SECONDS_IN_YEAR:
            return await ctx.respond("Reminders can only be up to 1 year.")

        # Handle short reminders
        if length <= 60:
            msg = await ctx.respond(f"Will remind you in {length} seconds.")
            await asyncio.sleep(length)
            return await ctx.respond(f"{ctx.author.mention}: {content}")

        # Otherwise create a new reminder
        starttime = int(time.time())
        endtime = starttime + length
        delta = timedelta(seconds=length)
        short_time_str = time.strftime('%H:%M:%S', time.gmtime(delta.seconds))
        msg = await ctx.respond((
            f"Will remind you in `{delta.days}:{short_time_str}`."))

        psql = """
                INSERT INTO reminders 
                    (starttime, endtime, user_id, content)
                VALUES ($1, $2, $3, $4);
                """
        async with self.bot.db.acquire() as conn:
            await conn.execute(psql, starttime, endtime, ctx.author.id, content)


def setup(bot):
    bot.add_cog(Reminders(bot))