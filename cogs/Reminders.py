import discord
from discord import Option

from discord.ext import commands, pages, tasks

import asyncio
import time
from datetime import timedelta

from Utilities import Vars


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

    # AUXILIARY FUNCTIONS
    def write(self, start, reminders, player):
        output = ''
        iteration = 0
        while start < len(reminders) and iteration < 5: #Loop til 5 entries or none left

            time_left=timedelta(seconds=reminders[start]['endtime']-time.time())

            days_left = ''
            if time_left.days == 1:
                days_left += '1 day, '
            elif time_left.days > 1:
                days_left += f'{time_left.days} days, '

            fmt = "%H hours, %M minutes, %S seconds"
            seconds = time.gmtime(time_left.seconds)
            time_str = time.strftime(fmt, seconds)

            output += (
                f"**ID: `{reminders[start]['id']}` | "
                f"In {days_left}{time_str}:**\n"
                f"{reminders[start]['content']}\n")
            
            iteration += 1
            start += 1

        embed = discord.Embed(title=f'{player}\'s Reminders',
            description = output,
            color = Vars.ABLUE)
        
        return embed

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
            4 : 86400, # days to seconds
        }
        for i in range(1, len(timer)+1):
            length += int(timer[-i]) * conv[i]
        
        SECONDS_IN_YEAR = 31536000
        if length > SECONDS_IN_YEAR:
            return await ctx.respond("Reminders can only be up to 1 year.")

        # Handle short reminders
        if length <= 60:
            await ctx.respond(f"Will remind you in {length} seconds.")
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

    @r.command(name="list", guild_ids=[762118688567984151])
    async def _list(self, ctx):
        """Show the list of your active reminders."""
        # Get person's active reminders
        psql = """
                SELECT id, starttime, endtime, user_id, content
                FROM reminders
                WHERE user_id = $1
                ORDER BY endtime;
                """
        async with self.bot.db.acquire() as conn:
            reminders = await conn.fetch(psql, ctx.author.id)

        if len(reminders) == 0:
            return await ctx.respond("You have no reminders!")

        remind_pages = [self.write(i, reminders, ctx.author.display_name)
            for i in range(0, len(reminders), 5)]

        if len(reminders) == 1:
            await ctx.respond(embed=remind_pages[0])
        else:
            paginator = pages.Paginator(pages=remind_pages, timeout=30.0)
            await paginator.respond(ctx.interaction)
        
    @r.command(guild_ids=[762118688567984151])
    async def delete(self, ctx, 
            reminder_id : Option(int,
                description="The ID of the reminder you want to delete.",
                required=True)):
        """Delete a reminder so that you are not reminded of it."""
        psql = """
                DELETE FROM reminders
                WHERE id = $1 AND user_id = $2;
                """
        async with self.bot.db.acquire() as conn:
            await conn.execute(psql, reminder_id, ctx.author.id)
        await ctx.respond(
            f"Deleted reminder `{reminder_id}` (if you created it).")
        

def setup(bot):
    bot.add_cog(Reminders(bot))