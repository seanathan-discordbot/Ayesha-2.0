import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages

from Utilities import Checks, Vars, PlayerObject, ItemObject

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

    
    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.HasChar)
    async def inventory(self, ctx,
            order : Option(str, description="Order by ATK or CRIT",
                default="attack", 
                choices=[
                    OptionChoice(name="attack"), 
                    OptionChoice(name="crit")]),
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
                psql2 += f""" 
                            AND rarity = $2 AND weapontype = $3
                            ORDER BY {order} DESC;
                            """
                inv = await conn.fetch(psql2, ctx.author.id, rarity, weapontype)
            elif rarity is not None and weapontype is None:
                psql2 += f""" 
                            AND rarity = $2
                            ORDER BY {order} DESC;
                            """
                inv = await conn.fetch(psql2, ctx.author.id, rarity)
            elif rarity is None and weapontype is not None:
                psql2 += f"""
                            AND weapontype = $2
                            ORDER BY {order} DESC;
                            """
                inv = await conn.fetch(psql2, ctx.author.id, weapontype)
            else:
                psql2 += f" ORDER BY {order} DESC;"
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
            paginator.customize_button("next", button_label=">", 
                button_style=discord.ButtonStyle.green)
            paginator.customize_button("prev", button_label="<", 
                button_style=discord.ButtonStyle.green)
            paginator.customize_button("first", button_label="<<", 
                button_style=discord.ButtonStyle.blurple)
            paginator.customize_button("last", button_label=">>", 
                button_style=discord.ButtonStyle.blurple)
            await paginator.send(ctx, ephemeral=False)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.HasChar)
    async def equip(self, ctx, item : Option(int, 
            description="The ID of the item you want to equip.",
            required=False)):
        """Equip an item using its ID (get from /inventory)"""
        await ctx.defer()

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if item:
                await player.equip_item(conn, item)
                await ctx.respond((
                    f"Equipped item {player.equipped_item.weapon_id}: "
                    f"{player.equipped_item.name} (ATK: "
                    f"{player.equipped_item.attack}, CRIT: "
                    f"{player.equipped_item.crit})"))
            else: # Unequip current item
                await player.unequip_item(conn)
                await ctx.respond("Unequipped your item.")

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.HasChar)
    async def merge(self, ctx, item : Option(int, 
                description="The ID of the item you want to strengthen."),
            fodder : Option(int, 
                description="The ID of the item you want to destroy.")):
        """Merge an item into another to boost its ATK by 1."""
        await ctx.defer() # I hate how I have to use this a lot
        
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

            await ctx.respond("Merge would be ok but I need to do tax rates to continue lol")

            # Calculate the cost of the merge
            # TODO implement tax rates
            


def setup(bot):
    bot.add_cog(Items(bot))