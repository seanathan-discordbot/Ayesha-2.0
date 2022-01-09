import discord
from discord.commands.commands import Option, OptionChoice
from discord.commands.context import ApplicationContext

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

import asyncio
import random
import schedule

from Utilities import Checks, Finances, ItemObject, PlayerObject, Vars

class Offices(commands.Cog):
    """Offices Text"""

    def __init__(self, bot):
        self.bot = bot

        async def update_offices():
            # Give payout to current mayor and comptroller
            async with self.bot.db.acquire() as conn:
                comp_rec = await PlayerObject.get_comptroller(conn)
                comptroller = await PlayerObject.get_player_by_id(
                    conn, comp_rec['officeholder'])
                mayor_rec = await PlayerObject.get_mayor(conn)
                mayor = await PlayerObject.get_player_by_id(
                    conn, mayor_rec['officeholder'])
                tax_info = await Finances.get_tax_info(conn)
                payout = int(tax_info['Collected'] / 100)
                await comptroller.give_gold(conn, payout)
                await mayor.give_gold(conn, payout)

                psql1 = """
                        WITH gravitas_leader AS (
                            SELECT user_id
                            FROM players
                            WHERE assc IN (
                                SELECT assc_id
                                FROM associations
                                WHERE assc_type = 'College'
                            )
                            ORDER BY gravitas DESC
                            LIMIT 1
                        )
                        INSERT INTO officeholders (officeholder, office)
                        VALUES ((SELECT user_id FROM gravitas_leader), 'Mayor')
                        RETURNING officeholder;
                        """
                psql2 = """
                        WITH gold_leader AS (
                            SELECT user_id
                            FROM players
                            WHERE assc IN (
                                SELECT assc_id
                                FROM associations
                                WHERE assc_type = 'Guild'
                            )
                            ORDER BY gold DESC
                            LIMIT 1
                        )
                        INSERT INTO officeholders (officeholder, office)
                        VALUES ((SELECT user_id FROM gold_leader), 'Comptroller')
                        RETURNING officeholder;
                        """
                new_mayor_id = await conn.fetchval(psql1)
                new_comp_id = await conn.fetchval(psql2)
                new_mayor = await self.bot.fetch_user(new_mayor_id)
                new_comp = await self.bot.fetch_user(new_comp_id)

                await self.bot.announcement_channel.send(
                    f"Congratulations to our new mayor {new_mayor.mention} and "
                    f"comptroller {new_comp.mention}, who will be serving "
                    f"Aramithea for this week!")

        def run_offices_func():
            asyncio.run_coroutine_threadsafe(update_offices(), self.bot.loop)

        async def schedule_office_updates():
            office_scheduler = schedule.Scheduler()
            office_scheduler.every().wednesday.at("12:00").do(run_offices_func)
            while True:
                office_scheduler.run_pending()
                await asyncio.sleep(office_scheduler.idle_seconds)

        asyncio.ensure_future(schedule_office_updates())


    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Offices is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    async def offices(self, ctx):
        """View the map, tax rate, and this week's elected officeholders."""
        async with self.bot.db.acquire() as conn:
            comptroller_rec = await PlayerObject.get_comptroller(conn)
            mayor_rec = await PlayerObject.get_mayor(conn)
            comptroller = await self.bot.fetch_user(
                comptroller_rec['officeholder'])
            mayor = await self.bot.fetch_user(mayor_rec['officeholder'])
            tax_info = await Finances.get_tax_info(conn)

        embed = discord.Embed(
            title=f"This Week's Officeholders!",
            color=Vars.ABLUE)
        embed.add_field(name="Mayor",
            value=f"{mayor.mention}: **{mayor_rec['user_name']}**")
        embed.add_field(name="Comptroller",
            value=f"{comptroller.mention}: **{comptroller_rec['user_name']}**")
        embed.add_field(
            name=f"Current Tax Rate: `{tax_info['tax_rate']}`%",
            value=(
                f"The mayor has collected `{tax_info['Collected']}` gold "
                f"so far this term."),
            inline=False)
        embed.set_image(url="https://i.imgur.com/jpLztYK.jpg")

        await ctx.respond(embed=embed)

    


def setup(bot):
    bot.add_cog(Offices(bot))