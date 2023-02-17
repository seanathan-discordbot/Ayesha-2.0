import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages

import asyncpg
import random
from typing import List

from Utilities import Checks, Vars, AcolyteObject, PlayerObject
from Utilities.AyeshaBot import Ayesha
from Utilities.ConfirmationMenu import ConfirmationMenu

def acolyte_equipped(player,acolyte_id):
    id_1=player.acolyte1.acolyte_id
    id_2=player.acolyte2.acolyte_id
    return (acolyte_id==id_1 or acolyte_id==id_2)

async def get_all_acolytes(conn : asyncpg.Connection, 
        user_id : int) -> List[AcolyteObject.Acolyte]:
    """Returns a list of 'AcolyteObject.Acolyte's the player with the ID owns"""
    psql = """
          SELECT acolyte_id
          FROM acolytes
          WHERE user_id = $1
          ORDER BY acolyte_name;
          """
    list_ids = await conn.fetch(psql, user_id)
    temp=[record['acolyte_id'] for record in list_ids]
    return [await AcolyteObject.get_acolyte_by_id(conn,id) for id in temp]

class Acolytes(commands.Cog):
    """
    All of the commands relating to Acolytes
    """
    def __init__(self, bot : Ayesha):
        self.bot=bot
    
    #events
    @commands.Cog.listener()
    async def on_ready(self):
        print("Acolyte is ready.")

    #add logic to add when not equipped
    def write(self, start : int, inv: List[AcolyteObject.Acolyte], 
            player : PlayerObject.Player) -> discord.Embed:
        """
        A helper function that creates the embeds for the tavern method
        """
        embed = discord.Embed(title=f'{player.char_name}\'s Tavern', 
                              color=Vars.ABLUE)
        iteration = 0
        while start < len(inv) and iteration < 5: 
            #Loop til 5 entries or none left
            info=inv[start].gen_dict
            #add whether acolyte is equipped or not. 
            if acolyte_equipped(player,inv[start].acolyte_id):
                embed.add_field(
                    name=f"{info['Name']}: `{inv[start].acolyte_id}` [EQUIPPED]",
                    value=(
                        f"**Attack:** {inv[start].get_attack()}, "
                        f"**Crit:** {inv[start].get_crit()}, "
                        f"**HP:** {inv[start].get_hp()}\n"
                        f"**Effect:** {info['Effect']}"),
                    inline=False)
            else:
                embed.add_field(
                    name=f"{info['Name']}: `{inv[start].acolyte_id}`",
                    value=(
                        f"**Attack:** {inv[start].get_attack()}, "
                        f"**Crit:** {inv[start].get_crit()}, "
                        f"**HP:** {inv[start].get_hp()}\n"
                        f"**Effect:** {info['Effect']}"),
                    inline=False)
            iteration += 1
            start += 1
        return embed
    
    # COMMANDS
    tavern = discord.commands.SlashCommandGroup("tavern", 
        "Acolyte-viweing commands")

    @tavern.command(name="list")
    async def _viewall(self, ctx : discord.ApplicationContext, 
            order : Option(str,
                description="List acolytes in a certain order",
                required=False,
                default="Oldest",
                choices=[
                    OptionChoice("First Recruited", "Oldest"),
                    OptionChoice("Last Recruited", "Newest"),
                    OptionChoice("Highest Attack", "Attack"),
                    OptionChoice("Highest Crit", "Crit"),
                    OptionChoice("Highest HP", "HP"),
                    OptionChoice("Not Yet Hired", "Unowned")
                ])):
        """View the list of acolytes"""
        psql = """
                SELECT uid, name AS acolyte_name, acolytes.user_id, 
                    acolytes.acolyte_id, attack, crit, hp, effect, story, image
                FROM acolyte_list
                LEFT JOIN acolytes 
                    ON acolyte_list.name = acolytes.acolyte_name 
                        AND acolytes.user_id = $1
                ORDER BY (acolytes.acolyte_id IS NOT NULL) DESC, uid;
               """
        # Creates the list of acolytes
        async with self.bot.db.acquire() as conn:
            acolytes = await conn.fetch(psql, ctx.author.id)
            new_acolytes = []
            for record in acolytes:
                if record['acolyte_id'] is not None:
                    new_acolytes.append(
                        await AcolyteObject.get_acolyte_by_id(
                            conn, record['acolyte_id']))
                else:
                    base_info = await AcolyteObject.Acolyte.get_acolyte_by_name(
                        record['acolyte_name'], conn)
                    new_acolytes.append(
                        AcolyteObject.Acolyte(record, base_info))
            acolytes = new_acolytes
        
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
        
        # Sort according to argument passed
        BIGN = 9223372036854775807
        match order:
            case "Oldest": # The or statements move `None` to the back
                acolytes.sort(key=lambda x : x.acolyte_id or BIGN)
            case "Newest":
                acolytes.sort(key=lambda x : x.acolyte_id or 0, reverse=True)
            case "Attack":
                acolytes.sort(key=lambda x : x.get_attack(), reverse=True)
            case "Crit":
                acolytes.sort(key=lambda x : x.get_crit(), reverse=True)
            case "HP":
                acolytes.sort(key=lambda x : x.get_hp(), reverse=True)
            case "Unowned":
                acolytes.sort(key=lambda x : x.acolyte_id is None, reverse=True)

        acolytes.sort( # Put the equipped acolytes at the top
            key=lambda x : x.acolyte_id in (
                player.acolyte1.acolyte_id, player.acolyte2.acolyte_id),
            reverse=True)

        # Display initial tavern embed
        embeds = [self.write(i, new_acolytes, player) 
            for i in range(0, len(acolytes), 5)]
        
        paginator = pages.Paginator(pages=embeds, timeout=30)
        await paginator.respond(ctx.interaction)

    @tavern.command()
    @commands.check(Checks.is_player)
    async def equip(self, ctx : discord.ApplicationContext,
            slot : Option(int, 
                description="The slot you want to add the acolyte to",
                choices = [
                    OptionChoice(name="Slot 1", value=1),
                    OptionChoice(name="Slot 2", value=2)]),
            name : Option(str, 
                description="The name of the acolyte you are adding to your party",
                max_length=32,
                required=False,
                autocomplete=lambda ctx : (
                    [name for name in ctx.bot.acolyte_list 
                     if ctx.value.lower() in name.lower()]))):
        """Equip or unequip an acolyte in a given slot."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if name is None: # Unequip from slot
                if slot == 1:
                    old_name = player.acolyte1.acolyte_name
                else:
                    old_name = player.acolyte2.acolyte_name
                await player.unequip_acolyte(conn, slot)
                return await ctx.respond(
                    f"**{old_name}** left slot {slot} of your party.")

            # Perform search for acolyte ID using the name
            name = name.title()
            all_acolytes = await get_all_acolytes(conn, ctx.author.id)
            ids = [a.acolyte_id for a in all_acolytes if name == a.acolyte_name]

            # Equip acolyte and send message
            if not ids:
                return await ctx.respond(
                    (f"There is no acolyte named **{name}** in your tavern."))

            await player.equip_acolyte(conn, ids[0], slot)

            get_str = lambda x : f"**{x}** joined your party in slot {slot}."
            if slot == 1:
                await ctx.respond(get_str(player.acolyte1.acolyte_name))
            else:
                await ctx.respond(get_str(player.acolyte2.acolyte_name))

    @tavern.command()
    @commands.check(Checks.is_player)
    async def recruit(self, ctx,
            name : Option(str, 
                description="The name of the acolyte you want to summon",
                max_length=32,
                autocomplete=lambda ctx : (
                    [name for name in ctx.bot.acolyte_list 
                        if ctx.value.lower() in name.lower()]))):
        """Spend 1 rubidic to add a new acolyte to your tavern!"""
        name = name.title()
        async with self.bot.db.acquire() as conn:
            # Ensure player has sufficient rubidics
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.rubidics < 1:
                raise Checks.NotEnoughResources("rubidics", 1, player.rubidics)

            # Validate acolyte being summoned
            try:
                acolyte_info = await AcolyteObject.Acolyte.get_acolyte_by_name(
                    name, conn)
            except TypeError:
                return await ctx.respond(
                    f"There is no such acolyte with the name **{name}**.")

            # Send confirmation box
            embed = discord.Embed(
                title=(
                    f"Are you sure you want to add {acolyte_info['Name']} "
                    "to your tavern?"),
                description=(
                    f"This action will cost `1` rubidic. You currently have "
                    f"`{player.rubidics}` rubidics. "),
                color=Vars.ABLUE)
            if acolyte_info['Image'] is not None:
                embed.set_thumbnail(url=acolyte_info['Image'])
            view = ConfirmationMenu(user=ctx.author, timeout=30.0)
            msg = await ctx.respond(embed=embed, view=view)

            await view.wait()
            if view.value is None:
                await msg.delete_original_message()
                return await ctx.respond("Timed out.")
            elif not view.value:
                await msg.delete_original_message()
                return await ctx.respond("Cancelled the transaction.")

            # Add acolyte to player's tavern
            try:
                new_acolyte = await AcolyteObject.create_acolyte(conn, 
                    ctx.author.id, name)
            except Checks.DuplicateAcolyte as e:
                return await msg.edit_original_message(
                    content=(
                        f"**{name}** (ID: `{e.original_id}`) is already in your "
                        "tavern. Try again with another acolyte that is not yet "
                        "in your tavern."),
                    embed=None,
                    view=None)
            
            # Create display embed and complete transaction
            embed=discord.Embed(
                title=(f"{new_acolyte.acolyte_name} (ID: "
                       f"`{new_acolyte.acolyte_id}`) has entered the tavern!"),
                color=Vars.ABLUE)
            if new_acolyte.gen_dict['Image'] is not None:
                embed.set_thumbnail(url=new_acolyte.gen_dict['Image'])
            embed.add_field(name="Attack",
                value=new_acolyte.gen_dict['Attack'])
            embed.add_field(name="Crit", value = new_acolyte.gen_dict['Crit'])
            embed.add_field(name="HP", value=new_acolyte.gen_dict['HP'])
            embed.add_field(name="Effect", value=new_acolyte.gen_dict['Effect'], 
                inline=False)
            embed.add_field(name="Backstory", value=new_acolyte.gen_dict['Story'], 
                inline=False)
            embed.set_footer(text=(
                f"To equip {new_acolyte.acolyte_name}, use their ID with the "
                f"/recruit command."))

            await msg.edit_original_message(embed=embed, view=None)
            await player.give_rubidics(conn, -1)


def setup(bot):
    bot.add_cog(Acolytes(bot))