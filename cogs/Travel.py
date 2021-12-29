import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

import random
import time

from Utilities import Checks, PlayerObject, ItemObject, Vars

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
                    destination=destination)

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
                await player.set_adventure(conn, time.time(), "EXPEDITION")
                message = (
                    "You have gone on an expedition! You can return at any "
                    "time by using the `/arrive` command. You will gain "
                    "increased rewards the longer you are on expedition, "
                    "for up to 1 week. Be sure to return by then!")
                await ctx.respond(message)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_travelling)
    async def arrive(self, ctx, 
            cancel : Option(str,
                description=
                    "Type 'Yes' to cancel your current adventure if travelling",
                required=False,
                options=[OptionChoice("Yes"), OptionChoice("No")],
                default="No")):
        """Complete your adventure/expedition and gain rewards!"""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            a = player.destination == "EXPEDITION"
            b = time.time() > player.adventure # Travel done if b and !a
            c = cancel == "Yes"
            if not a and c: # Cancel travel regardless of completion
                await player.set_adventure(conn, None, None)
                await ctx.respond("You cancelled your adventure.")

            elif not a and not b and not c: # Travel isn't done yet
                diff = self.int_to_time(int(player.adventure - time.time()))
                message = (
                    f"You are still travelling to **{player.destination}** and "
                    f"will arrive there in `{diff}.`")
                await ctx.respond(message)

            elif not a and b and not c: # End the adventure - give rewards
                # Calculate what to give
                length = Vars.TRAVEL_LOCATIONS[player.location]\
                    ['Destinations'][player.destination]
                rewards = self.calculate_travel_rewards(length)
                gold = random.randint(rewards['gold_low'], rewards['gold_high'])
                xp = random.randint(rewards['xp_low'], rewards['xp_high'])
                if player.occupation == "Traveler":
                    gold *= 3
                    xp *= 3
                if rewards['weapon'] >= random.randint(1,100):
                    new_weapon = await ItemObject.create_weapon(
                        conn=conn,
                        user_id=player.disc_id,
                        rarity="Common")
                else:
                    new_weapon = ItemObject.Weapon()

                # Give the rewards
                message = (
                    f"You arrived at **{player.destination}**! On the way "
                    f"you earned `{gold}` gold and `{xp}` xp! ")
                if not new_weapon.is_empty:
                    message += (
                        f"You also found a weapon: \n"
                        f"`{new_weapon.weapon_id}`: {new_weapon.name}, "
                        f"a {new_weapon.rarity} {new_weapon.type} with "
                        f"`{new_weapon.attack}` ATK and `{new_weapon.crit}` "
                        f"CRIT.")
                # Sending this first so level-up messages come after
                await ctx.respond(message) 
                await player.give_gold(conn, gold)
                await player.check_xp_increase(conn, ctx, xp)
                await player.set_location(conn, player.destination)
                await player.set_adventure(conn, None, None)
                

            else: # End the expedition, nothing really matters for this one
                await ctx.respond("Expedition ended (WIP)")


def setup(bot):
    bot.add_cog(Travel(bot))