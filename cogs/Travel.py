import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

from Utilities import Checks, PlayerObject, Vars

class Travel(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Travel is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
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
                if destination is None:
                    return await ctx.respond(
                        "You must pick a destination to travel to!")
                elif destination == player.location:
                    return await ctx.respond(
                        f"You are already at **{player.location}**!")
                    
                time_length = Vars.TRAVEL_LOCATIONS[player.location]\
                    ['Destinations'][destination] # grrr

                await ctx.respond(f"Your adventure will go on for {time_length} seconds.")

            else:
                await ctx.respond("You went on expedition.")



def setup(bot):
    bot.add_cog(Travel(bot))