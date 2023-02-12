import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages

import asyncpg
import random
from typing import List

from Utilities import Checks, Vars, AcolyteObject, PlayerObject
from Utilities.AyeshaBot import Ayesha
from Utilities.ConfirmationMenu import LockedConfirmationMenu

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
    def generic_write(self, start : int, inv : List[asyncpg.Record]):
        """Write function like below, but for the `/acolyte` command."""
        embed = discord.Embed(title=f"Attainable Acolytes", color=Vars.ABLUE)
        iteration = 0
        while start < len(inv) and iteration < 5:
            info = inv[start]
            embed.add_field(
                name=f"`{info['uid']}`: {info['name']}",
                value=(
                    f"**Attack:** {info['attack']}, "
                    f"**Crit:** {info['crit']}, "
                    f"**HP:** {info['hp']}\n"
                    f"**Effect:** {info['effect']}"),
                inline=False)
            iteration += 1
            start += 1
        return embed

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
    @commands.slash_command()
    async def acolyte(self, ctx,
        name : Option(str, 
            description="The name of the acolyte you are viewing",
            required=False)):
        """View an acolyte's general information."""
        # Give a list of all acolytes if no name is given
        if name is None:
            async with self.bot.db.acquire() as conn:
                psql = """
                        SELECT uid, name, attack, crit, hp, effect
                        FROM acolyte_list
                        ORDER BY uid;
                        """
                acolytes = await conn.fetch(psql)

            embeds = []
            for i in range(0, len(acolytes), 5):
                embeds.append(self.generic_write(i, acolytes))

            paginator = pages.Paginator(pages=embeds, timeout=30)
            return await paginator.respond(ctx.interaction)

        # Otherwise get acolyte asked for
        name = name.title()
        try:
            async with self.bot.db.acquire() as conn:
                acolyte_info = await AcolyteObject.Acolyte.get_acolyte_by_name(
                    name, conn)
        except TypeError:
            return await ctx.respond(
                f"There is no such acolyte with the name {name}."
            )
        
        embed = discord.Embed(            
                title=acolyte_info["Name"],
                color=Vars.ABLUE)

        if acolyte_info["Image"] is not None:
            embed.set_thumbnail(url=acolyte_info["Image"])
        embed.add_field(name="Backstory", value=acolyte_info["Story"])
        embed.add_field(
            name="Effect", 
            value=acolyte_info["Effect"], 
            inline=False)
        embed.add_field(name="Stats",
            value=(
                f"Attack: {acolyte_info['Attack']}\n"
                f"Crit: {acolyte_info['Crit']} \n"
                f"HP: {acolyte_info['HP']}"))
        await ctx.respond(embed=embed)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def tavern(self, ctx,
            order : Option(str,
                description="Sorts your tavern in a specific way",
                required=False,
                default="Name",
                choices=[
                    OptionChoice("Order by Attack", "Attack"),
                    OptionChoice("Order by Crit", "Crit"),
                ])):
        """View a list of all your owned acolytes."""
        async with self.bot.db.acquire() as conn:
            acolytes= await get_all_acolytes(conn, ctx.author.id)

            if order == "Attack":
                acolytes.sort(key=lambda a : a.get_attack(), reverse=True)
            elif order == "Crit":
                acolytes.sort(key=lambda a : a.get_crit(), reverse=True)
            else: # Sort by name by default
                acolytes.sort(key=lambda a : a.acolyte_name)

            player=await PlayerObject.get_player_by_id(conn, ctx.author.id)
            embeds = []
            for i in range(0, len(acolytes), 5): #list 5 entries at a time
                embeds.append(self.write(i, acolytes, player))
            if len(embeds) == 0:
                await ctx.respond('Your tavern is empty!')
            elif len(embeds) == 1:
                await ctx.respond(embed=embeds[0])
            else:
                paginator = pages.Paginator(pages=embeds, timeout=30)
                await paginator.respond(ctx.interaction)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def recruit(self, ctx,
            slot : Option(int, 
                description="The slot you want to add the acolyte to",
                choices = [
                    OptionChoice(name="Slot 1", value=1),
                    OptionChoice(name="Slot 2", value=2)]),
            instance_id : Option(int, 
                description="Id of acolyte to add to slot",
                required=False)):
        """Equip or unequip an acolyte in a given slot."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if instance_id is None: # Unequip from slot
                await player.unequip_acolyte(conn,slot)
                return await ctx.respond("Unequipped acolyte.")

            await player.equip_acolyte(conn, instance_id, slot)

            if slot == 1:
                await ctx.respond(
                    f"Equipped acolyte: {player.acolyte1.acolyte_name}")
            else:
                await ctx.respond(
                    f"Equipped acolyte: {player.acolyte2.acolyte_name}")

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def summon(self, ctx,
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

            # Add acolyte to player's tavern
            try:
                new_acolyte = await AcolyteObject.create_acolyte(conn, ctx.author.id, name)
            except Checks.DuplicateAcolyte as e:
                return await ctx.respond((
                    f"**{name}** (ID: `{e.original_id}`) is already in your "
                    "tavern. Try again with another acolyte that is not yet "
                    "in your tavern."))
            
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

            await ctx.respond(embed=embed)
            await player.give_rubidics(conn, -1)

def setup(bot):
    bot.add_cog(Acolytes(bot))