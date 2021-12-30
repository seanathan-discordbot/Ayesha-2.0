from os import name
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
                # Calculate what to give
                elapsed = int(time.time() - player.adventure)
                hours = 168 if elapsed > 604800 else elapsed / 3600

                if hours < 1: # 100 gold/hr, 50 xp/hr, no gravitas
                    gold = int(hours * 100)
                    xp = int(hours * 50)
                    mats = random.randint(5, 10)
                    gravitas = 0
                    gravitas_decay = .01
                elif hours < 6: # 125 gold/hr, 55 xp/hr, no gravitas
                    gold = int(hours * 125)
                    xp = int(hours * 55)
                    mats = int(hours * 10)
                    gravitas = 0
                    gravitas_decay = .05
                elif hours < 24: # 150 gold/hr, 60 xp/hr, 1/6 gravitas/hr
                    gold = int(hours * 150)
                    xp = int(hours * 60)
                    mats = int(hours * 15)
                    gravitas = int(hours / 6)
                    gravitas_decay = .1
                elif hours < 72: # 175 gold/hr, 70 xp/hr, 1/4 gravitas/hr
                    gold = int(hours * 175)
                    xp = int(hours * 70)
                    mats = int(hours * 20)
                    gravitas = int(hours / 4)
                    gravitas_decay = .15
                elif hours < 144: # 200 gold/hr, 85 xp/hr, 1/3 gravitas/hr
                    gold = int(hours * 200)
                    xp = int(hours * 85)
                    mats = int(hours * 25)
                    gravitas = int(hours / 3)
                    gravitas_decay = .2
                else: # 250 gold/hr, 100 xp/hr, 1/2 gravitas/hr
                    gold = int(hours * 250)
                    xp = int(hours * 100)
                    mats = int(hours * 30)
                    gravitas = int(hours / 2)
                    gravitas_decay = .25

                # Create the embed to send
                embed = discord.Embed(title="Expedition Complete!", 
                    color=Vars.ABLUE)
                embed.set_thumbnail(url=ctx.author.avatar.url)
                e_message = (
                    f"While on your journey, you gained these resources:\n"
                    f"Gold: `{gold}`\n"
                    f"EXP: `{xp}`\n")

                # Give player the goods
                await player.give_gold(conn, gold)
                if player.location in ("Aramithea", "Riverburn", "Thenuille"):
                    resource = random.choice(['fur', 'bone'])
                    mats = int(mats/4)
                    e_name = "You returned from your urban expedition"
                    e_message += (
                        f"Your campaign increased your gravitas by "
                        f"`{gravitas}`.\n")
                else:
                    gravitas = player.gravitas * gravitas_decay * -1
                    e_name = "You returned from your expedition"
                    e_message += (
                        f"Your gravitas decreased by `{gravitas*-1}` while "
                        f"in the wilderness.\n")
                    if player.location == "Mythic Forest":
                        resource = "wood"
                    elif player.location in ("Fernheim", "Croire"):
                        resource = "wheat"
                    elif player.location in ("Sunset Prairie", "Glakelys"):
                        resource = "oat"
                    elif player.location == "Thanderlans":
                        resource = "reeds"
                    elif player.location == "Russe":
                        resource = random.choice(["pine", "moss"])
                    elif player.location == "Crumidia":
                        resource = "silver"
                    else: # Kucre, and any bugs I miss lol
                        resource = "cacao"

                e_message += f"You gained `{mats}` {resource}.\n"
                # TODO: Implement Traveler getting acolyte bonus
                await player.give_resource(conn, resource, mats)
                await player.give_gravitas(conn, gravitas)
                await player.set_adventure(conn, None, None)
                embed.add_field(name=e_name, value=e_message)
                await ctx.respond(embed=embed)
                await player.check_xp_increase(conn, ctx, xp)


def setup(bot):
    bot.add_cog(Travel(bot))