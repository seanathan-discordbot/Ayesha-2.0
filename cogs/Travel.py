import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

import time

from Utilities import Checks, PlayerObject, Vars

class Travel(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Travel is ready.")

    # AUXILIARY FUNCTIONS
    def int_to_time(self, seconds : int):
        """Converts a time.time() to a strftime (HH:MM:SS)"""
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def calculate_travel_rewards(self, time_length : int) -> dict:
        """Given the time length and the player's occupation, create a dict
        which gives the forecasted rewards for completing an adventure.
        Dict: gold_low, gold_high, xp_low, xp_high
        """
        return {
            'gold_low' : int((time_length**1.5)/1250),
            'gold_high' : int((time_length**1.5)/1000),
            'xp_low' : int((time_length**1.5)/350),
            'xp_high' : int((time_length**1.5)/250),
            'weapon' : 5 if time_length <= 7200 else 10
        }


    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_not_travelling)
    async def travel(self, ctx, 
            type : Option(str, 
                description="The type of adventure you will go on",
                choices = [OptionChoice("Travel"), OptionChoice("Expedition")],
                default="Travel"),
            destination : Option(str,
                description="The part of the map you are travelling to",
                choices = [OptionChoice(name=t) 
                    for t in Vars.TRAVEL_LOCATIONS.keys()],
                required=False
            )):
        """Travel to a new area on the map, or go on an expediture in place."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            if type == "Travel":
                # Make sure traveling is a valid option
                if destination is None:
                    return await ctx.respond(
                        "You must pick a destination to travel to!")
                elif destination == player.location:
                    return await ctx.respond(
                        f"You are already at **{player.location}**!")
                    
                # Start the adventure
                time_length = Vars.TRAVEL_LOCATIONS[player.location]\
                    ['Destinations'][destination] # grrr
                await player.set_adventure(conn, 
                    adventure=int(time_length + time.time()), 
                    destination=destination, 
                    user_id=player.disc_id)

                # Tell user adventure began
                rewards = self.calculate_travel_rewards(time_length)
                embed = discord.Embed(title="Your Adventure Has Begun",
                    color=Vars.ABLUE)
                # embed.set_thumbnail(
                #     url=Vars.TRAVEL_LOCATIONS[destination]['Image'])
                embed.add_field(
                    name=(
                        f"You will arrive at {destination} in "
                        f"`{self.int_to_time(time_length)}`."),
                    value=(
                        f"**You are projected to gain these along the way:**\n"
                        f"Gold: `{rewards['gold_low']}-"
                        f"{rewards['gold_high']}`\n"
                        f"EXP: `{rewards['xp_low']}-{rewards['xp_high']}`\n"
                        f"These rewards can be tripled if you are a "
                        f"**Traveler**.\n\n"
                        f"You have a `{rewards['weapon']}%` chance of finding "
                        f"a weapon along the way!"))

                await ctx.respond(embed=embed)

            else:
                await ctx.respond("You went on expedition.")



def setup(bot):
    bot.add_cog(Travel(bot))