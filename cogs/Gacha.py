import discord
from discord import Option, OptionChoice

from discord.ext import commands

import asyncpg

from Utilities import Checks, Vars, PlayerObject, AcolyteObject, ItemObject
from Utilities.Finances import Transaction
from Utilities.AyeshaBot import Ayesha

class SummonDropdown(discord.ui.Select):
    def __init__(self, results : list, author_id : int):
        self.results = results
        self.author_id = author_id
        options = [discord.SelectOption(label=results[i][0], value=str(i)) 
            for i in range(len(results))]
        super().__init__(options = options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return

        await interaction.response.edit_message(
            embed=self.results[int(self.values[0])][1])

class Gacha(commands.Cog):
    """Spend rubidics and gold for random items"""

    def __init__(self, bot : Ayesha):
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

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Gacha is ready.")

    # COMMANDS

    @commands.slash_command()
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

    ex_mats = [OptionChoice(m) for m in Vars.MATERIALS]
    ex_mats.append(OptionChoice("Gold"))
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def exchange(self, ctx, 
            offer : Option(str,
                description=f"The material you want to trade away",
                choices=[OptionChoice(m) for m in Vars.MATERIALS]),
            amount : Option(int,
                description=f"The amount of the material you are exchanging",
                min_value=20),
            want : Option(str,
                description=f"The material you want to receive",
                choices=ex_mats)):
        """Exchange 10 of your excess resources for 1 gold or another resource."""
        # Check for valid input
        if offer == want:
            return await ctx.respond(f"This is an unfavorable trade.")
        offer = offer.lower()
        want = want.lower()

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            amount -= amount % 10 # Make a multiple of 20 so nothing is wasted
            to_receive = amount // 10

            if player.resources[offer] < amount:
                raise Checks.NotEnoughResources(
                    offer, amount, player.resources[offer])

            # Complete transaction
            await player.give_resource(conn, offer, amount*-1)
            if want == "gold":
                sale = await Transaction.create_sale(conn, player, to_receive)
                print_tax = await sale.log_transaction(conn, "sale")
            else:
                print_tax = ""
                await player.give_resource(conn, want, to_receive)

        await ctx.respond((
            f"You exchanged `{amount}` **{offer}** for `{to_receive}` "
            f"**{want}**. {print_tax}"))


def setup(bot):
    bot.add_cog(Gacha(bot))