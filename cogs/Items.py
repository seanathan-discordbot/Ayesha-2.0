import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages

import random

from Utilities import Checks, Vars, PlayerObject, ItemObject
from Utilities.Analytics import stringify_gains
from Utilities.ConfirmationMenu import ConfirmationMenu
from Utilities.Finances import Transaction
from Utilities.AyeshaBot import Ayesha

class Items(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot : Ayesha):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Items is ready.")

    # AUXILIARY FUNCTIONS
    def create_embed(self, source, title, field_write_func, items_per_page):
        """Create a list of embeds with the source given

        Parameters
        ----------
        source : Iterable
            the contents that are being made into an embed
        title : str
            the title of the embed
        field_write_func : Callable
            the function that will populate the embed fields
            will be passed the record it is making a field for
            must return a dictionary with the following keys: name, value, inline
        items_per_page : int
            the amount of items that will be listed on each embed

        Returns
        -------
        embeds : List[discord.Embed]
            A list of discord Embeds made with the contents of `source`        
        """
        if not source:
            return [discord.Embed(title="Your inventory is empty!", color=Vars.ABLUE)]

        embeds = []

        source_size = len(source)
        
        for i in range(0, source_size, items_per_page):
            embed = discord.Embed(title=title, color=Vars.ABLUE)
            embed.set_footer(text=f"{source_size} items listed.")

            current = i
            items_in_page = 0
            while current < source_size and items_in_page < items_per_page:
                field_values = field_write_func(source[current])
                embed.add_field(**field_values)
                items_in_page += 1
                current += 1
            
            embeds.append(embed)
        
        return embeds

    def weapons_field_values(self, record) -> dict:
        name = f"{record['weapon_name']}: `{record['item_id']}` "
        name += "EQUIPPED" if record['equipped'] else ""
        value = (
            f"**Attack:** {record['attack']}, **Crit:** "
            f"{record['crit']}, **Type:** "
            f"{record['weapontype']}")
        return {"name" : name, "value" : value, "inline" : False}

    def armor_field_values(self, record) -> dict:
        mat = record['armor_type']
        slot = record['armor_slot']
        name = f"{mat} {slot}: `{record['armor_id']}` "
        name += "[EQUIPPED]" if record['equipped'] else ""
        value=f"**Defense:** {Vars.ARMOR_DEFENSE[slot][mat]}%"
        return {"name" : name, "value" : value, "inline" : False}

    def accessory_field_values(self, record : ItemObject.Accessory):
        name = f"{record.name}: `{record.id}` "
        name += "[EQUIPPED]" if record.equipped else ""
        value=record.bonus
        return {"name" : name, "value" : value, "inline" : False}
    

    # COMMANDS
    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def inventory(self, ctx,
            weapon_order : Option(str, description="Order by ATK or Crit",
                default="item_id",
                choices=[
                    OptionChoice(name="Attack", value="attack"),
                    OptionChoice(name="Crit", value="crit"),
                    OptionChoice(name="ID", value="item_id")],
                required=False),
            weapon_type : Option(str, description="Get only a specific weapontype",
                choices=[OptionChoice(name=t) for t in Vars.WEAPON_TYPES],
                required=False),
            armor_type : Option(str, description="Get only a specific armor slot",
                choices=[OptionChoice(s) for s in Vars.ARMOR_DEFENSE],
                required=False),
            armor_material : Option(str, description="Get only a specific armor material",
                choices=[OptionChoice(m) for m in Vars.ARMOR_DEFENSE["Boots"]],
                required=False),
            accessory_effect : Option(str, description="Sort for a specific effect",
                choices=[OptionChoice(p) for p in Vars.ACCESSORY_BONUS],
                required=False),
            accessory_material : Option(str, description="Sort for a specific core material",
                choices=[OptionChoice(m) for m in Vars.ACCESSORY_BONUS['Lucky']],
                required=False)):
        """View your complete inventory, including weapons, armor, and accessories."""
        await ctx.defer()
        # Get the query for inventory based on input
        weapons_query = f"""
            SELECT item_id, weapontype, user_id, attack, crit, weapon_name,
                (
                    item_id = (
                        SELECT equipped_item 
                        FROM players 
                        WHERE user_id = $1
                    )
                ) 
                AS equipped
            FROM items
            WHERE user_id = $1
                {f"AND weapontype = '{weapon_type}'"
                    if weapon_type is not None else ""}
            ORDER BY equipped DESC, {weapon_order} DESC;
            """
        # Indicator of bad database design choices
        armor_query = f"""
            WITH helmet AS (SELECT helmet FROM equips WHERE user_id = $1),
            bodypiece AS (SELECT bodypiece FROM equips WHERE user_id = $1),
            boots AS (SELECT boots FROM equips WHERE user_id = $1)
            SELECT armor_id, armor_type, armor_slot,
                CASE
                    WHEN armor_slot = 'Helmet' 
                    THEN armor_id = (SELECT * FROM helmet)
                    ELSE CASE
                        WHEN armor_slot = 'Bodypiece' 
                        THEN armor_id = (SELECT * FROM bodypiece)
                        ELSE CASE
                            WHEN armor_slot = 'Boots' 
                            THEN armor_id = (SELECT * FROM boots)
                            ELSE false
                        END
                    END
                END
                AS equipped
            FROM armor
            WHERE user_id = $1
                {f"AND armor_slot = '{armor_type}'"
                    if armor_type is not None else ""}
                {f"AND armor_type = '{armor_material}'"
                    if armor_material is not None else ""}
            ORDER BY equipped DESC, armor_id DESC;
            """
        accessory_query = f"""
            SELECT accessory_id, 
                (
                    accessory_id = (
                        SELECT accessory FROM equips WHERE user_id = $1
                    )
                ) 
                AS equipped
            FROM accessories
            WHERE user_id = $1
                {f"AND prefix = '{accessory_effect}'"
                    if accessory_effect is not None else ""}
                {f"AND accessory_type = '{accessory_material}'"
                    if accessory_material is not None else ""}
            ORDER BY equipped DESC, accessory_id DESC; 
            """

        # Pull relevant records from db
        async with self.bot.db.acquire() as conn:
            weapons = await conn.fetch(weapons_query, ctx.author.id)

            armory = await conn.fetch(armor_query, ctx.author.id)

            accessories = await conn.fetch(accessory_query, ctx.author.id)
            wardrobe_items = []
            for accessory in accessories:
                temp = await ItemObject.get_accessory_by_id(conn, accessory['accessory_id'])
                temp.equipped = accessory['equipped']
                wardrobe_items.append(temp)
            accessories = wardrobe_items

        inventory_embeds = self.create_embed(weapons, "Your Weapons", 
            self.weapons_field_values, 5)
        armor_embeds = self.create_embed(armory, "Your Armor", 
            self.armor_field_values, 5)
        accessory_embeds = self.create_embed(accessories, "Your Accessories", 
            self.accessory_field_values, 5)

        weapon_pages = pages.PageGroup(pages=inventory_embeds, label="View Weapons")
        armor_pages = pages.PageGroup(pages=armor_embeds, label="View Armor")
        accessory_pages = pages.PageGroup(pages=accessory_embeds, label="View Accessories")

        # Display to player
        paginator = pages.Paginator(
            pages=[weapon_pages, armor_pages, accessory_pages], 
            show_menu=True,
            menu_placeholder="Select type of item to view")
        await paginator.respond(ctx.interaction, ephemeral=False)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def equip(self, ctx, 
            equip : Option(str,
                description="Equip either a weapon or armor",
                choices=[
                    OptionChoice("Equip a Weapon"), 
                    OptionChoice("Equip Armor"),
                    OptionChoice("Equip an Accessory")]),
            id : Option(int, 
                description="The ID of the item you want to equip.",
                required=False)):
        """Equip an item using its ID (get from /inventory if weapon, /armory if armor)"""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            if equip == "Equip a Weapon" and id is not None:
                await player.equip_item(conn, id)
                await ctx.respond((
                    f"Equipped item `{player.equipped_item.weapon_id}`: "
                    f"{player.equipped_item.name} (ATK: "
                    f"{player.equipped_item.attack}, CRIT: "
                    f"{player.equipped_item.crit})"))
            elif equip == "Equip Armor" and id is not None:
                armor = await player.equip_armor(conn, id)
                await ctx.respond((
                    f"Equipped armor `{armor.id}`: {armor.name} "
                    f"(DEF: `{armor.defense}%`)"))
            elif equip == "Equip an Accessory" and id is not None:
                await player.equip_accessory(conn, id)
                await ctx.respond((
                    f"Equipped accessory `{player.accessory.id}`: "
                    f"{player.accessory.name}: {player.accessory.bonus}."))

            elif equip == "Equip a Weapon" and id is None:
                await player.unequip_item(conn)
                await ctx.respond("Unequipped your item.")
            elif equip == "Equip Armor" and id is None:
                await player.unequip_armor(conn)
                await ctx.respond("Unequipped all your armor.")
            else:
                await player.unequip_accessory(conn)
                await ctx.respond("Unequipped your accessory.")

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def merge(self, ctx, item : Option(int, 
                description="The ID of the item you want to strengthen."),
            fodder : Option(int, 
                description="The ID of the item you want to destroy.")):
        """Merge an item into another to boost its ATK by 1."""
        if item == fodder:
            return await ctx.respond("You cannot merge an item with itself.")
        
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            # Make sure players owns these items
            a = await player.is_weapon_owner(conn, item)
            b = await player.is_weapon_owner(conn, fodder)
            if not a or not b:
                raise Checks.NotWeaponOwner
            
            # Make sure fodder is not the equipped item
            if fodder == player.equipped_item.weapon_id:
                return await ctx.respond(
                    "You can't use your equipped item as fodder!")

            # Load weapons and make sure they are merge eligible
            # Same weapontype, and fodder at least 15 ATK less than item
            item_w = await ItemObject.get_weapon_by_id(conn, item)
            fodder_w = await ItemObject.get_weapon_by_id(conn, fodder)

            if item_w.type != fodder_w.type:
                return await ctx.respond(
                    "These items must have the same weapontype to be merged.")
            
            if fodder_w.attack < item_w.attack - 15:
                return await ctx.respond((
                    "The fodder item must have at least 15 less ATK than the "
                    "item being upgraded."))

            # Calculate the cost of the merge
            purchase = await Transaction.calc_cost(conn, player, 10000)
            if purchase.paying_price > player.gold:
                return await ctx.respond((
                    f"You need at least `{purchase.paying_price}` gold to "
                    f"perform this operation. You currently have "
                    f"`{player.gold}` gold."))
            
            # Perform the merge
            atk_bonus_sources = []
            if player.occupation == "Blacksmith":
                new_atk = item_w.attack + 2
                atk_bonus_sources.append((1, "Blacksmith"))
            else:
                new_atk = item_w.attack + 1
            await item_w.set_attack(conn, new_atk)
            await fodder_w.destroy(conn)
            print_tax = await purchase.log_transaction(conn, "purchase")

        atk_gain_str = stringify_gains("ATK", 1, atk_bonus_sources)
        await ctx.respond((
            f"You buffed your **{item_w.name}** by {atk_gain_str} to "
            f"`{item_w.attack}`.\n"
            f"This cost you `10000` gold.\n{print_tax}"))

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def sell(self, ctx, 
            item_type : Option(str,
                description="The type of item you are selling",
                choices=[
                    OptionChoice("Sell a Weapon", "weapon"),
                    OptionChoice("Sell Armor", "armor"),
                    OptionChoice("Sell an Accessory", "accessory")]),
            item_id : Option(int, 
                description="The ID of the item you want to sell",
                required=False),
            attack : Option(int,
                description="Sell all weapons with an ATK stat below this one",
                required=False,
                min_value=10
            ),
            crit : Option(int,
                description="Sell all weapons with a CRIT stat below this one",
                required=False,
                min_value=0
            )
            ):
        """Sell an item (pass ID), or sell multiple items below a threshold."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            if item_type in ("armor", "accessory") and item_id is None:
                return await ctx.respond(
                    f"Please enter the ID of the {item_type} you are selling.")
            
            elif item_type == "armor":
                eq_ar = (player.helmet.id, player.bodypiece.id, player.boots.id)
                if item_id in eq_ar:
                    return await ctx.respond(
                        "Don't sell your equipped armor!")
                if not await player.is_armor_owner(conn, item_id):
                    raise Checks.NotArmorOwner
                item = await ItemObject.get_armor_by_id(conn, item_id)
                # Make armor sale
                gold = random.randint(
                    a=Vars.ARMOR_SALE_PRICES[item.type]['low'],
                    b=Vars.ARMOR_SALE_PRICES[item.type]['high'])
                sale = await Transaction.create_sale(conn, player, gold)
                print_tax = await sale.log_transaction(conn, "sale")
                await item.destroy(conn)
                gold_gain_str = stringify_gains(
                    "gold", sale.subtotal, sale.bonus_list)
                return await ctx.respond((
                    f"You sold your `{item_id}`: {item.name} and made "
                    f"{gold_gain_str}.\n{print_tax}"))

            elif item_type == "accessory":
                if item_id == player.accessory.id:
                    return await ctx.respond(
                        "Don't sell your equipped accessory!")
                if not await player.is_accessory_owner(conn, item_id):
                    raise Checks.NotAccessoryOwner
                item = await ItemObject.get_accessory_by_id(conn, item_id)
                # Make accessory sale
                gold = random.randint(
                    a=Vars.ACCESSORY_SALE_PRICES[item.type]["low"],
                    b=Vars.ACCESSORY_SALE_PRICES[item.type]["high"])
                sale = await Transaction.create_sale(conn, player, gold)
                print_tax = await sale.log_transaction(conn, "sale")
                await item.destroy(conn)
                gold_gain_str = stringify_gains(
                    "gold", sale.subtotal, sale.bonus_list)
                return await ctx.respond((
                    f"You sold your `{item_id}`: {item.name} and made "
                    f"{gold_gain_str}.\n{print_tax}"))

            # SELL WEAPON 
            if item_id is not None: # If they pass both, only sell the item ID
                # See if this is an eligible sale
                if player.equipped_item.weapon_id == item_id:
                    return await ctx.respond(
                        "Don't sell your equipped item!")
                if not await player.is_weapon_owner(conn, item_id):
                    raise Checks.NotWeaponOwner
                item = await ItemObject.get_weapon_by_id(conn, item_id)

                # Make the sale
                gold = random.randint(a=500, b=3000)
                sale = await Transaction.create_sale(conn, player, gold)
                print_tax = await sale.log_transaction(conn, "sale")
                await item.destroy(conn)
                gold_gain_str = stringify_gains(
                    "gold", sale.subtotal, sale.bonus_list)
                await ctx.respond((
                    f"You sold your `{item_id}`: {item.name} and made "
                    f"{gold_gain_str}.\n{print_tax}"))

            elif attack is not None or crit is not None:
                psql = f"""
                        WITH deleted AS (
                            DELETE FROM items
                            WHERE user_id = $1 AND item_id NOT IN ($2)
                                {f"AND attack < {attack}"
                                    if attack is not None else ""}
                                {f"AND crit < {crit}"
                                    if crit is not None else ""}
                            RETURNING item_id
                        )
                        SELECT COUNT(*)
                        FROM deleted;
                        """
                amount_sold = await conn.fetchval(psql, player.disc_id, 
                    player.equipped_item.weapon_id)

                if amount_sold == 0:
                    return await ctx.respond(
                        "You have no items of this quality to sell!")

                subtotal = random.randint(a=500*amount_sold, b=3000*amount_sold)
                sale = await Transaction.create_sale(conn, player, subtotal)
                print_tax = await sale.log_transaction(conn, "sale")
                gold_gain_str = stringify_gains(
                    "gold", sale.subtotal, sale.bonus_list)
                await ctx.respond((
                    f"You sold all {amount_sold} of your weapons of this "
                    f"quality and made {gold_gain_str}.\n{print_tax}"))

            else: # Then they passed nothing
                await ctx.respond("You didn't pass anything to sell.")

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def offer(self, ctx,
            player : Option(discord.Member,
                description="The player you want to give something to",
                converter=commands.MemberConverter()),
            price : Option(int,
                description="The price you are charging for your offer",
                min_value=0),
            sale_type : Option(str,
                description="What you are selling",
                choices=[
                    OptionChoice("Sell a Weapon", "Weapon"),
                    OptionChoice("Sell Armor", "Armor")]),
            item_id : Option(int,
                description="The ID of the weapon you are offering")):
        """Offer an item or gold to another player."""
        async with self.bot.db.acquire() as conn:
            author = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            player_char = await PlayerObject.get_player_by_id(conn, player.id)
            # Check for valid input
            if player_char.gold < price:
                return await ctx.respond(
                    f"This player cannot afford your price.")

            message = f"{player.mention}, {ctx.author.mention} is offering you "

            # Check item to see if its sellable
            if sale_type == "Weapon":
                if item_id == author.equipped_item.weapon_id:
                    return await ctx.respond("Don't sell your equipped item!")
                if not await author.is_weapon_owner(conn, item_id):
                    raise Checks.NotWeaponOwner
                item = await ItemObject.get_weapon_by_id(conn, item_id)
            else:
                eq_ar = (author.helmet.id, author.bodypiece.id, author.boots.id)
                if item_id in eq_ar:
                    return await ctx.respond("Don't sell your equipped armor!")
                if not await author.is_armor_owner(conn, item_id):
                    raise Checks.NotArmorOwner
                item = await ItemObject.get_armor_by_id(conn, item_id)
                
            # Load item and offer message
            if sale_type == "Weapon":
                message += f"the weapon:\n"
                message += f"`{item.weapon_id}`: {item.name}, a {item.type} "
                message += f"with `{item.attack}` ATK and `{item.crit}` CRIT.\n"
            else:
                message += (
                    f"this armor:\n"
                    f"`{item.id}`: {item.name}, with `{item.defense}` DEF.\n")

            message += (
                f"They are charging you `{price}` gold. Do you accept?\n"
                f"(You currently have `{player_char.gold}` gold.)")

            # Send player the offer
            view = ConfirmationMenu(user=player, timeout=30.0)
            self.bot.trading_players[ctx.author.id] = 0
            msg = await ctx.respond(content=message, view=view)
            await view.wait()
            if view.value is None:
                await ctx.respond("Timed out.")
            elif view.value and not item.is_empty: # Works for Weapon and Armor
                await item.set_owner(conn, player_char.disc_id)
                await player_char.give_gold(conn, price*-1)
                await author.give_gold(conn, price)
                await ctx.respond("They accepted the offer.")
            else:
                await ctx.respond("They declined your offer.")
            await msg.delete_original_message()
            self.bot.trading_players.pop(ctx.author.id)


def setup(bot):
    bot.add_cog(Items(bot))