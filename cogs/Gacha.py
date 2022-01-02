import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

import asyncpg
import json
import random

from Utilities import Checks, Vars, PlayerObject, AcolyteObject, ItemObject
from Utilities.Finances import Transaction

class Gacha(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot):
        self.bot = bot
        self.rarities = None
        self.int_rar_to_str = {
            1 : "Common",
            2 : "Uncommon",
            3 : "Rare",
            4 : "Epic",
            5 : "Legendary"
        }
        self.armor_costs = {
            "Cloth" : 2500,
            "Wood" : 5000,
            "Silk" : 8000,
            "Leather" : 20000,
            "Gambeson" : 25000,
            "Bronze" : 50000,
            "Ceramic Plate" : 70000,
            "Chainmail" : 75000,
            "Iron" : 100000
        } # Be sure to change the OptionChoices in shop if changing this

        # Get a list of all acolytes sorted by rarity
        with open(Vars.ACOLYTE_LIST_PATH) as f:
            acolyte_list = json.load(f)
            self.rarities = {i:[] for i in range(1,6)}
            for acolyte in acolyte_list:
                self.rarities[acolyte_list[acolyte]['Rarity']].append(acolyte)

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Gacha is ready.")

    # INVISIBLE
    async def roll_acolyte(self, conn : asyncpg.Connection, 
            player : PlayerObject.Player, 
            rarity : int) -> discord.Embed:
        """Creates a random acolyte of the specified rarity.
        Returns an embed listing the acolyte's information.
        """
        acolyte_name = random.choice(self.rarities[rarity])
        acolyte =  await AcolyteObject.create_acolyte(
            conn, player.disc_id, acolyte_name)

        embed=discord.Embed(
            title=(
                f"{acolyte.acolyte_name} ({acolyte.gen_dict['Rarity']}) has "
                f"entered the tavern!"),
            color=Vars.ABLUE)
        embed.set_thumbnail(url=acolyte.gen_dict['Image'])
        embed.add_field(name="Attack",
            value=f"{acolyte.gen_dict['Attack']} + {acolyte.gen_dict['Scale']}")
        embed.add_field(name="Crit", value = acolyte.gen_dict['Crit'])
        embed.add_field(name="HP", value=acolyte.gen_dict['HP'])
        embed.add_field(name="Effect",
            value=(
                f"{acolyte.gen_dict['Effect']}\n {acolyte.acolyte_name} uses `"
                f"{acolyte.gen_dict['Mat']}` to level up."))
        return embed

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def summon(self, ctx, 
            pulls : Option(int,
                description="Do up to 10 pull at once!",
                required=False,
                min_value=1,
                max_value=10,
                default=1)):
        """Spend 1 rubidics to get a random acolyte or weapon."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.rubidics < pulls:
                raise Checks.NotEnoughResources("rubidics", 
                    pulls, player.rubidics)

            # This essentially calculates the results (type and rarity)
            r_types = random.choices(
                population=["weapon", "acolyte"],
                weights=[75, 25],
                k=pulls)
            r_rarities = random.choices(
                population=range(1,6),
                weights=[1, 60, 35, 3, 1],
                k=pulls)

            # Simulate the pulls by creating new objects
            embed_list = []
            for i in range(pulls):
                if player.pity_counter >= 79:
                    # Give 5 star acolyte
                    embed_list.append(await self.roll_acolyte(conn, player, 5))
                    player.pity_counter = 0
                    continue

                # Create a random new weapon or acolyte
                # Write an embed for this and add it to the list
                if r_types[i] == "acolyte":
                    embed_list.append(await self.roll_acolyte(
                        conn, player, r_rarities[i]))

                else:
                    weapon = await ItemObject.create_weapon(
                        conn=conn,
                        user_id=player.disc_id,
                        rarity=self.int_rar_to_str[r_rarities[i]])

                    embed=discord.Embed(
                        title=f"You received {weapon.name} ({weapon.rarity})",
                        color=Vars.ABLUE)
                    embed.add_field(name="Type", value=weapon.type)
                    embed.add_field(name="Attack", value=weapon.attack)
                    embed.add_field(name="Crit", value=weapon.crit)
                    embed_list.append(embed)

                player.pity_counter += 1 # Temp change, not stored in db

            for embed in embed_list:
                embed.set_footer(text=(
                    f"You have {player.rubidics-pulls} rubidics. You will "
                    f"receive a 5-star acolyte in {80-player.pity_counter} "
                    f"summons."))

            # Update player's rubidics and pity counter
            await player.give_rubidics(conn, pulls*-1)
            await player.set_pity_counter(conn, player.pity_counter)

            # Paginate embeds if pulls > 1 and print them
            if len(embed_list) > 1:
                paginator = pages.Paginator(pages=embed_list, timeout=30)
                paginator.customize_button("next", button_label=">", 
                    button_style=discord.ButtonStyle.green)
                paginator.customize_button("prev", button_label="<", 
                    button_style=discord.ButtonStyle.green)
                paginator.customize_button("first", button_label="<<", 
                    button_style=discord.ButtonStyle.blurple)
                paginator.customize_button("last", button_label=">>", 
                    button_style=discord.ButtonStyle.blurple)
                await paginator.send(ctx, ephemeral=False)
            else:
                await ctx.respond(embed=embed_list[0])

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def shop(self, ctx,
            armor : Option(str,
                description="The type of armor you are buying",
                choices=[OptionChoice(t) for t in Vars.ARMOR_DEFENSE]),
            material : Option(str,
                description="The material of the armor you want",
                choices=[
                    OptionChoice("Cloth Armor (2,500 gold)", "Cloth"),
                    OptionChoice("Wooden Armor (5,000 gold)", "Wood"),
                    OptionChoice("Silk Armor (8,000 gold)", "Silk"),
                    OptionChoice("Leather Armor (20,000 gold)", "Leather"),
                    OptionChoice("Gambeson Armor (25,000 gold)", "Gambeson"),
                    OptionChoice("Bronze Armor (50,000 gold)", "Bronze"),
                    OptionChoice("Ceramic Plate Armor (70,000 gold)", 
                        "Ceramic Plate"),
                    OptionChoice("Chainmail Armor (75,000 gold)", "Chainmail"),
                    OptionChoice("Iron Armor (100,000 gold)", "Iron")])):
        """Exchange your extra gold for some other stuff!"""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            purchase = await Transaction.calc_cost(
                conn, player, self.armor_costs[material])

            if purchase.paying_price > player.gold:
                raise Checks.NotEnoughGold(purchase.paying_price, player.gold)

            item = await ItemObject.create_armor(conn, player.disc_id, armor, material)
            print_tax = await purchase.log_transaction(conn, "purchase")

            await ctx.respond((
                f"You purchased `{item.id}`: {item.name}. Use the `/equip` "
                f"command to equip it!\n"
                f"This purchase cost `{purchase.subtotal}` gold. {print_tax}"))


def setup(bot):
    bot.add_cog(Gacha(bot))