import discord
from discord import Option

from discord.ext import commands, tasks

import asyncio
import time
from datetime import timedelta


class Reminders(commands.Cog):
    """Reminders text"""

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    @tasks.loop(seconds=15.0)
    async def check_for_reminders(self):
        # Every 15 seconds, get every reminder that has passed
        now = int(time.time())
        psql = """
                DELETE FROM reminders
                WHERE endtime <= $1
                RETURNING starttime, user_id, content;
                """
        async with self.bot.db.acquire() as conn:
            reminders = await conn.fetch(psql, now)

        # DM each reminder
        for reminder in reminders:
            # Get the person in question
            user = await self.bot.fetch_user(reminder['user_id'])

            # Create a string telling them the time passed
            elapsed_time = now - reminder['starttime']
            delta = timedelta(seconds=elapsed_time)
            days = f"0{delta.days}" if delta.days < 10 else str(delta.days)
            short_elapsed = time.gmtime(elapsed_time % 86400)
            time_str = days + ":" + time.strftime("%H:%M:%S", short_elapsed)

            # Send a DM
            if not user.dm_channel:
                await user.create_dm()
            await user.send((
                f"`{time_str}` ago, you wanted to be reminded of:\n"
                f"{reminder['content']}"))

    
    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        self.check_for_reminders.start()
        print("Reminders is ready.")

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
        await ctx.respond((
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