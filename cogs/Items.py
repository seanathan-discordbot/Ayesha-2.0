import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages

import random

from Utilities import Checks, Vars, PlayerObject, ItemObject, Finances
from Utilities.Finances import Transaction

class OfferView(discord.ui.View):
    """Help me. Same code as Profile.ConfirmButton. Bad code moment"""
    def __init__(self, target : discord.Member):
        super().__init__(timeout=15.0)
        self.value = None
        self.target = target

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.target.id

class Items(commands.Cog):
    """View and manipulate your inventory"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Items is ready.")

    # AUXILIARY FUNCTIONS
    def create_embed(self, start, inv, got_eq):
        embed = discord.Embed(title=f"Your Inventory", color=Vars.ABLUE)

        iteration = 0
        while start < len(inv) and iteration < 5:
            if got_eq and start == 0:
                embed.add_field(name=(
                        f"{inv[start]['weapon_name']}: `{inv[start]['item_id']}` "
                        f"[EQUIPPED]"),
                    value=(
                        f"**Attack:** {inv[start]['attack']}, **Crit:** "
                        f"{inv[start]['crit']}, **Type:** "
                        f"{inv[start]['weapontype']}, **Rarity:** "
                        f"{inv[start]['rarity']}"
                    ),
                    inline=False)
            else:
                embed.add_field(name=(
                        f"{inv[start]['weapon_name']}: `{inv[start]['item_id']}` "
                        ),
                    value=(
                        f"**Attack:** {inv[start]['attack']}, **Crit:** "
                        f"{inv[start]['crit']}, **Type:** "
                        f"{inv[start]['weapontype']}, **Rarity:** "
                        f"{inv[start]['rarity']}"
                    ),
                    inline=False)
            iteration += 1
            start += 1
        return embed

    def create_armor_embed(self, start, inv):
        embed = discord.Embed(title="Your Armory", color=Vars.ABLUE)

        iteration = 0
        while start < len(inv) and iteration < 5:
            mat = inv[start]['armor_type']
            slot = inv[start]['armor_slot']
            embed.add_field(
                name=f"{mat} {slot}: `{inv[start]['armor_id']}`",
                value=f"**Defense:** {Vars.ARMOR_DEFENSE[slot][mat]}%",
                inline=False)
            iteration += 1
            start += 1
        
        return embed

    def create_accessory_embed(self, start, inv):
        embed = discord.Embed(title="Your Wardrobe", color=Vars.ABLUE)

        iteration = 0
        while start < len(inv) and iteration < 5:
            embed.add_field(
                name=f"{inv[start].name}: `{inv[start].id}`",
                value=inv[start].bonus,
                inline=False)
            iteration += 1
            start += 1

        return embed
    
    # COMMANDS
    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def inventory(self, ctx,
            order : Option(str, description="Order by ATK or CRIT",
                default="ID", 
                choices=[
                    OptionChoice(name="attack"), 
                    OptionChoice(name="crit"),
                    OptionChoice(name="ID")],
                required=False),
            rarity : Option(str, description="Get only a specific rarity",
                choices=[OptionChoice(name=r) for r in Vars.RARITIES.keys()],
                required=False),
            weapontype : Option(str, 
                description="Get only a specific weapon type",
                choices=[OptionChoice(name=t) for t in Vars.WEAPON_TYPES],
                required=False)):
        """View your inventory."""
        await ctx.defer()

        async with self.bot.db.acquire() as conn:
            # Get equipped item to put at top of list
            psql1 = """
                    WITH thing AS (
                        SELECT equipped_item
                        FROM players
                        WHERE user_id = $1
                    )
                    SELECT items.item_id, items.weapontype, items.user_id, 
                        items.attack, items.crit, items.weapon_name, 
                        items.rarity
                    FROM items
                    INNER JOIN thing ON items.item_id = thing.equipped_item;
                    """
            psql2 = """
                    SELECT item_id, weapontype, user_id, 
                        attack, crit, weapon_name, rarity
                    FROM items
                    WHERE user_id = $1
                    """

            if rarity is not None and weapontype is not None:
                psql2 += f" AND rarity = $2 AND weapontype = $3 "
                if order == "ID":
                    psql2 += "ORDER BY item_id;"
                else:
                    psql2 += f"ORDER BY {order} DESC;"
                inv = await conn.fetch(psql2, ctx.author.id, rarity, weapontype)
            elif rarity is not None and weapontype is None:
                psql2 += f" AND rarity = $2 "
                if order == "ID":
                    psql2 += "ORDER BY item_id;"
                else:
                    psql2 += f"ORDER BY {order} DESC;"
                inv = await conn.fetch(psql2, ctx.author.id, rarity)
            elif rarity is None and weapontype is not None:
                psql2 += f"AND weapontype = $2"
                if order == "ID":
                    psql2 += "ORDER BY item_id;"
                else:
                    psql2 += f"ORDER BY {order} DESC;"
                inv = await conn.fetch(psql2, ctx.author.id, weapontype)
            else:
                if order == "ID":
                    psql2 += "ORDER BY item_id;"
                else:
                    psql2 += f"ORDER BY {order} DESC;"
                inv = await conn.fetch(psql2, ctx.author.id)

            equip = await conn.fetchrow(psql1, ctx.author.id)
            if equip is not None:
                got_eq = True
            else:
                got_eq = False

        inventory = [] # Allows me to put equip and rest of items in one thing
        for record in inv:
            inventory.append(record)

        if len(inventory) == 0: # Account for equipped item as 1
            return await ctx.respond("Your inventory is empty!")
        else: # Create a bunch of embeds and paginate
            if got_eq:
                inventory.insert(0, equip)
            # The create_embed function writes embeds; 5 per page
            embeds = [self.create_embed(i, inventory, got_eq) 
                for i in range(0, len(inventory), 5)]

            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def armory(self, ctx,
        slot : Option(str,
            description="Get only a specific armor slot",
            required=False,
            choices=[OptionChoice(s) for s in Vars.ARMOR_DEFENSE]),
        material : Option(str,
            description="Get only a specific armor material",
            required=False,
            choices=[OptionChoice(m) for m in Vars.ARMOR_DEFENSE["Boots"]])):
        """Armories held both weapons and armor, but here only armor :P"""
        await ctx.defer()
        async with self.bot.db.acquire() as conn:
            psql = f"""
                    SELECT armor_id, armor_type, armor_slot
                    FROM armor
                    WHERE user_id = $1 
                    """

            if slot is not None and material is not None:
                psql += """ 
                        AND armor_type = $2 AND armor_slot = $3
                        ORDER BY armor_id;
                        """
                armory = await conn.fetch(psql, ctx.author.id, material, slot)
            elif slot is not None and material is None:
                psql += """
                        AND armor_slot = $2
                        ORDER BY armor_id;
                        """
                armory = await conn.fetch(psql, ctx.author.id, slot)
            elif slot is None and material is not None:
                psql += """
                        AND armor_type = $2
                        ORDER BY armor_id;
                        """
                armory = await conn.fetch(psql, ctx.author.id, material)
            else:
                psql += " ORDER BY armor_id;"
                armory = await conn.fetch(psql, ctx.author.id)

        if len(armory) == 0:
            return await ctx.respond("Your armory is empty!")

        embeds = [self.create_armor_embed(i, armory) 
            for i in range(0, len(armory), 5)]
        if len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def wardrobe(self, ctx, 
            prefix : Option(str,
                description="Sort for a specific effect",
                required=False,
                choices=[OptionChoice(p) for p in Vars.ACCESSORY_BONUS]),
            material : Option(str,
                description="Sort for a specific core material",
                required=False,
                choices=[OptionChoice(m) for m in Vars.ACCESSORY_BONUS['Lucky']]
            )):
        """Your wardrobe contains all your accessories. View them here."""
        async with self.bot.db.acquire() as conn:
            psql = """
                    SELECT accessory_id
                    FROM accessories
                    WHERE user_id = $1 
                    """
            if prefix is not None and material is not None:
                psql += """
                        AND prefix = $2 AND accessory_type = $3
                        ORDER BY accessory_id;
                        """
                inv = await conn.fetch(psql, ctx.author.id, prefix, material)
            elif prefix is None and material is not None:
                psql += """
                        AND accessory_type = $2
                        ORDER BY accessory_id;
                        """
                inv = await conn.fetch(psql, ctx.author.id, material)
            elif prefix is not None and material is None:
                psql += """
                        AND prefix = $2
                        ORDER BY accessory_id;
                        """
                inv = await conn.fetch(psql, ctx.author.id, prefix)
            else:
                psql += " ORDER BY accessory_id;"
                inv = await conn.fetch(psql, ctx.author.id)

            if len(inv) == 0:
                return await ctx.respond("Your wardrobe is empty!")

            inv = [await ItemObject.get_accessory_by_id(
                        conn, record['accessory_id'])
                    for record in inv] # Turn them into objects (for the name)

        embeds = [self.create_accessory_embed(i, inv)
            for i in range(0, len(inv), 5)]
        if len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

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
            if player.occupation == "Blacksmith":
                new_atk = item_w.attack + 2
            else:
                new_atk = item_w.attack + 1
            await item_w.set_attack(conn, new_atk)
            await fodder_w.destroy(conn)
            print_tax = await purchase.log_transaction(conn, "purchase")

        await ctx.respond((
            f"You buffed your **{item_w.name}** to `{item_w.attack}` ATK.\n"
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
            rarity : Option(str,
                description="The rarity of the items you want to sell",
                choices=[OptionChoice(name=r) for r in Vars.RARITIES.keys()],
                required=False)
            ):
        """Sell an item (pass ID), or sell multiple items of some rarity."""
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
                return await ctx.respond((
                    f"You sold your `{item_id}`: {item.name} amd made "
                    f"`{sale.subtotal}` gold.\n{print_tax}"))

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
                return await ctx.respond((
                    f"You sold your `{item_id}`: {item.name} amd made "
                    f"`{sale.subtotal}` gold.\n{print_tax}"))

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
                gold = random.randint(a=Vars.RARITIES[item.rarity]['low_gold'], 
                    b=Vars.RARITIES[item.rarity]['high_gold'])
                sale = await Transaction.create_sale(conn, player, gold)
                print_tax = await sale.log_transaction(conn, "sale")
                await item.destroy(conn)
                await ctx.respond((
                    f"You sold your `{item_id}`: {item.name} and made "
                    f"`{sale.subtotal}` gold.\n{print_tax}"))

            elif rarity is not None: 
                psql = """
                        WITH deleted AS (
                            DELETE FROM items
                            WHERE user_id = $1 AND item_id NOT IN ($2)
                                AND rarity = $3
                            RETURNING item_id
                        )
                        SELECT COUNT(*)
                        FROM deleted;
                        """
                # This is an enormous optimization from the old version :)
                amount_sold = await conn.fetchval(psql, player.disc_id, 
                    player.equipped_item.weapon_id, rarity)

                if amount_sold == 0:
                    return await ctx.respond(
                        "You have no items of this rarity to sell!")

                subtotal = random.randint(a=Vars.RARITIES[rarity]['low_gold'], 
                    b=Vars.RARITIES[rarity]['high_gold'])
                subtotal *= amount_sold
                sale = await Transaction.create_sale(conn, player, subtotal)
                print_tax = await sale.log_transaction(conn, "sale")
                await ctx.respond((
                    f"You sould all {amount_sold} of your {rarity.lower()} "
                    f"items and made `{sale.subtotal}` gold.\n{print_tax}"))

            else: # Then they passed nothing bruh
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
                message += f"`{item.weapon_id}`: {item.name}, a {item.rarity} "
                message += f"{item.type} with `{item.attack}` ATK and "
                message += f"`{item.crit}` CRIT.\n"
            else:
                message += (
                    f"this armor:\n"
                    f"`{item.id}`: {item.name}, with `{item.defense}` DEF.\n")

            message += (
                f"They are charging you `{price}` gold. Do you accept?\n"
                f"(You currently have `{player_char.gold}` gold.)")

            # Send player the offer
            view = OfferView(target=player)
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