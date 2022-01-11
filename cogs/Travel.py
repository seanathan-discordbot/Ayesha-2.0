import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands

import json
import random
import time

from Utilities import AcolyteObject, AssociationObject, Checks, PlayerObject, ItemObject, Vars
from Utilities.Finances import Transaction

class Travel(commands.Cog):
    """Go on an adventure!"""

    def __init__(self, bot):
        self.bot = bot
        self.rarities = None

        # Get a list of all acolytes sorted by rarity - same code as in Gacha
        with open(Vars.ACOLYTE_LIST_PATH) as f:
            acolyte_list = json.load(f)
            self.rarities = {i:[] for i in range(1,6)}
            for acolyte in acolyte_list:
                self.rarities[acolyte_list[acolyte]['Rarity']].append(acolyte)


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
                choices = [OptionChoice("Travel Somewhere New"), 
                    OptionChoice("Go on an Expedition")],
                default="Travel"),
            destination : Option(str,
                description="The part of the map you are travelling to",
                choices = [
                    OptionChoice(
                        name=f"{t} ({Vars.TRAVEL_LOCATIONS[t]['Biome']})",
                        value=t) 
                    for t in Vars.TRAVEL_LOCATIONS.keys()],
                required=False
            )):
        """Travel to a new area on the map, or go on an expediture in place."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            if type == "Travel Somewhere New":
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

            # TRAVEL TYPE ADV IS OVER
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
                if player.accessory.prefix == "Lucky":
                    mult = Vars.ACCESSORY_BONUS["Lucky"][player.accessory.type]
                    xp = int(xp * (mult / 100.0))
                    gold = int(gold * (mult / 100.0))
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
                
            # EXPEDITION TYPE ADV IS OVER
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
                
                # Farmer gets reduced loss or bonus on expedition
                if player.occupation == "Farmer":
                    gravitas = int(gravitas * 1.2)
                    gravitas_decay *= 1/2
                # Accessory bonus
                if player.accessory.prefix == "Lucky":
                    mult = Vars.ACCESSORY_BONUS["Lucky"][player.accessory.type]
                    xp = int(xp * (mult / 100.0))
                    gold = int(gold * (mult / 100.0))

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
                    gravitas = int(player.gravitas * gravitas_decay * -1)
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
                # Traveler 50% chance to get acolyte on long expeditions
                right_occ = player.occupation == "Traveler"
                a = hours >= 72 and random.randint(1, 2) == 1
                b = hours >= 144 and random.randint(1, 2) == 1
                if right_occ and (a or b):
                    rarity = random.choices(range(1,6), (1, 60, 35, 3, 1))[0]
                    name = random.choice(self.rarities[rarity])
                    acolyte = await AcolyteObject.create_acolyte(
                        conn, player.disc_id, name)
                    e_message += (
                        f"During your expedition you befriended a new acolyte: "
                        f"{acolyte.acolyte_name} ({rarity}⭐)")
                await player.give_resource(conn, resource, mats)
                await player.give_gravitas(conn, gravitas)
                await player.set_adventure(conn, None, None)
                embed.add_field(name=e_name, value=e_message)
                await ctx.respond(embed=embed)
                await player.check_xp_increase(conn, ctx, xp)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def work(self, ctx, 
            workplace : Option(str,
                description="What type of work you want to do",
                choices=[
                    OptionChoice(name="Smalltown Gig"),
                    OptionChoice(name="Hunting Trip"),
                    OptionChoice(name="Mining Shift"),
                    OptionChoice(name="Foraging Party"),
                    OptionChoice(name="Fishing Getaway")
                ])):
        """Get a short gig to make some quick money or get resources."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            location_biome = Vars.TRAVEL_LOCATIONS[player.location]['Biome']
            result = random.choices(("success", "critical success", "failure"),
                (60, 10, 30))[0]
            if result == "success":
                bonus = 1 # Bonus will add all possible bonuses into one
            elif result == "critical success":
                bonus = 1.5
            else:
                bonus = .5
            # Brotherhood Map Control Bonus
            bonus_bh = await AssociationObject.get_territory_controller(
                conn, player.location)
            if player.assc.id == bonus_bh.id:
                bonus += .5

            if workplace == "Smalltown Gig":
                employer = random.choice((
                    "blacksmith", "cartographer's study", "library", "manor",
                    "doctor's office", "carpenter's studio", "art studio",
                    "farm", "general goods store", "bar", "tailor", "mill"))
                income = random.randint(20, 40) # No cooldowns so low income :/
                await player.give_gold(conn, income)
                await ctx.respond((f"You did a job at a nearby {employer} and "
                    f"made `{income}` gold."))

            elif workplace == "Hunting Trip":
                if location_biome not in ("Grassland", "Forest", "Taiga"):
                    return await ctx.respond((
                        f"You cannot hunt at **{player.location}**. Please "
                        f"move to a grassland, forest, or taiga."))
                
                if player.occupation == "Hunter":
                    bonus += 1
                if player.equipped_item.type == "Bow":
                    bonus += 1
                elif player.equipped_item.type == "Gauntlets":
                    bonus -= .5
                elif player.equipped_item.type == "Sling":
                    bonus += .5
                elif player.equipped_item.type == "Javelin":
                    bonus += .25

                income = int(random.randint(1, 10) * bonus)
                fur = int(random.randint(3, 8) * bonus)
                bone = int(random.randint(2, 6) * bonus)
                await player.give_gold(conn, income)
                await player.give_resource(conn, "fur", fur)
                await player.give_resource(conn, "bone", bone)
                await ctx.respond((
                    f"Your hunting trip was a {result}! You got `{income}` "
                    f"gold, `{fur}` fur, and `{bone}` bones."))

            elif workplace == "Mining Shift":
                if location_biome != "Hills":
                    return await ctx.respond((
                        f"You cannot mine at **{player.location}**. Please "
                        f"move to a hilly region."))

                if player.occupation == "Blacksmith":
                    bonus += 1
                if player.equipped_item.type == "Dagger":
                    bonus -= .25
                elif player.equipped_item.type in ("Bow", "Sling"):
                    bonus -= .5
                elif player.equipped_item.type == "Trebuchet":
                    bonus += 1
                elif player.equipped_item.type in ("Greatsword", "Axe", "Mace"):
                    bonus += .25

                income = int(random.randint(1,10) * bonus)
                iron = int(random.randint(7, 12) * bonus)
                silver = int(random.randint(2, 8) * bonus)
                await player.give_gold(conn, income)
                await player.give_resource(conn, "iron", iron)
                await player.give_resource(conn, "silver", silver)
                await ctx.respond((
                    f"Your mining expedition was a {result}! You got "
                    f"`{income}` gold, `{iron}` iron, and `{silver}` silver."))

            elif workplace == "Foraging Party":
                if location_biome in ("City", "Town"):
                    return await ctx.respond((
                        f"You foraged in **{player.location}** and found "
                        f"nothing but trash. Get outside of an urban area!"))
                elif player.location in ("Fernheim", "Croire"):
                    res = "wheat"
                    amount = random.randint(5, 12)
                elif player.location in ("Sunset Prairie", "Glakelys"):
                    res = "oat"
                    amount = random.randint(2, 6)
                elif location_biome == "Forest":
                    res = "wood"
                    amount = random.randint(3, 10)
                elif location_biome == "Marsh":
                    res = "reeds"
                    amount = random.randint(12, 24)
                elif location_biome == "Taiga":
                    res = random.choices(["pine", "moss"], [2, 1])[0]
                    amount = random.randint(9, 13)
                elif location_biome == "Hills":
                    res = "iron"
                    amount = random.randint(7, 12)
                elif location_biome == "Jungle":
                    res = "cacao"
                    amount = random.randint(2, 4)

                if player.occupation == "Traveller":
                    bonus += 1
                if player.equipped_item.type == "Dagger":
                    bonus += .1

                await player.give_resource(conn, res, int(amount * bonus))
                await ctx.respond((
                    f"You received `{amount}` {res} while foraging in "
                    f"**{player.location}**."))

            elif workplace == "Fishing Getaway":
                if player.location == "Thenuille":
                    result = random.choices(
                        ['🐟','🐠','🐡','🦈','🦦','nothing'], 
                        [45, 25, 6, 3, 1, 20])[0]
                else:
                    result = random.choices(
                        ['🐟','🐠','🐡','nothing'], 
                        [40, 15, 5, 40])[0]
                
                if result == "nothing":
                    await ctx.respond("You waited but did not catch anything.")
                elif result == '🦦':
                    await player.give_gold(conn, 1000)
                    await ctx.respond(
                        f"You caught {result}? It gave you a gold coin before "
                        f"jumping back into the water.")
                else:
                    if result == '🐟':
                        gold = random.randint(3, 9)
                    elif result == '🐠':
                        gold = random.randint(9, 18)
                    elif result == '🐡':
                        gold = random.randint(6, 15)
                    elif result == '🦈':
                        gold = random.randint(300, 400)
                    
                    await player.give_gold(conn, gold)
                    await ctx.respond((
                        f"You caught a {result}! You sould your prize for "
                        f"`{gold}` gold."))
            
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def upgrade(self, ctx, 
            weapon_id : Option(int, 
                name="weapon",
                description="The ID of the weapon you are upgrading"),
            iter : Option(int,
                name="iterations",
                description="The amount of times to upgrade this weapon",
                required=False,
                min_value=1,
                max_value=15,
                default=1)):
        """Upgrade a weapon's ATK stat. Costs 8*ATK iron and 35*ATK gold."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.location not in ("Aramithea", "Riverburn", "Thenuille"):
                return await ctx.respond(
                    "You can only upgrade items in an urban center!")

            # Make sure player actually owns this weapon
            if not await player.is_weapon_owner(conn, weapon_id):
                raise Checks.NotWeaponOwner
            
            # Is item eligible for an upgrade?
            weapon = await ItemObject.get_weapon_by_id(conn, weapon_id)
            if weapon.rarity == "Common" and weapon.attack + iter > 50:
                return await ctx.respond(
                    "Common weapons can only have a maximum ATK of `50`.")
            elif weapon.rarity == "Uncommon" and weapon.attack + iter > 75:
                return await ctx.respond(
                    "Uncommon weapons can only have a maximum ATK of `75`.")
            elif weapon.rarity == "Rare" and weapon.attack + iter > 100:
                return await ctx.respond(
                    "Rare weapons can only have a maximum ATK of `100`.")
            elif weapon.rarity == "Epic" and weapon.attack + iter > 125:
                return await ctx.respond(
                    "Epic weapons can only have a maximum ATK of `125`.")
            elif weapon.rarity == "Legendary" and weapon.attack + iter > 160:
                return await ctx.respond(
                    "Legendary weapons can only be upgraded to `160` ATK. "
                    "Use the `/merge` command to progress further.")

            # Calculate the costs of such an operation
            iron_cost, gold_cost = 0, 0
            for i in range(iter):
                iron_cost += 8 * (weapon.attack + i)
                gold_cost += 35 * (weapon.attack + i)
            verb = "time" if iter == 1 else "times"

            purchase = await Transaction.calc_cost(conn, player, gold_cost)

            if player.gold < purchase.paying_price:
                raise Checks.NotEnoughGold(purchase.paying_price, player.gold)
            if player.resources["iron"] < iron_cost:
                raise Checks.NotEnoughResources(
                    "iron", iron_cost, player.resources["iron"])

            # If all else clears, upgrade the item
            await weapon.set_attack(conn, weapon.attack + iter)
            print_tax = await purchase.log_transaction(conn, "purchase")
            await player.give_resource(conn, "iron", iron_cost*-1)
            await ctx.respond((
                f"You upgraded your `{weapon.weapon_id}`: {weapon.name} "
                f"{iter} {verb} for `{purchase.paying_price}` gold and "
                f"`{iron_cost}` iron, increasing its ATK to "
                f"`{weapon.attack}`! {print_tax}"))

def setup(bot):
    bot.add_cog(Travel(bot))