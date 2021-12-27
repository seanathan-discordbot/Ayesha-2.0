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
                    OptionChoice(name="attack"), OptionChoice(name="crit")]
                ),
            rarity : Option(str, description="Get only a specific rarity",
                choices=[OptionChoice(name="Legendary"), 
                    OptionChoice(name="Epic"), OptionChoice(name="Rare"),
                    OptionChoice(name="Uncommon"), OptionChoice(name="Common")])
    ):
        """View your inventory."""
        await ctx.defer()

        # Get equipped item to put at top of list
        psql1 = """
                WITH thing AS (
                    SELECT equipped_item
                    FROM players
                    WHERE user_id = $1
                )
                SELECT items.item_id, items.weapontype, items.user_id, 
                    items.attack, items.crit, items.weapon_name, items.rarity
                FROM items
                INNER JOIN thing ON items.item_id = thing.equipped_item;
                """
        psql2 = f"""
                SELECT item_id, weapontype, user_id, 
                    attack, crit, weapon_name, rarity
                FROM items
                WHERE user_id = $1 AND rarity = $2
                ORDER BY {order} DESC;
                """

        async with self.bot.db.acquire() as conn:
            inventory = []
            equip = await conn.fetchrow(psql1, ctx.author.id)
            if equip is not None:
                got_eq = True
            else:
                got_eq = False
            inv = await conn.fetch(psql2, ctx.author.id, rarity)

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


def setup(bot):
    bot.add_cog(Items(bot))