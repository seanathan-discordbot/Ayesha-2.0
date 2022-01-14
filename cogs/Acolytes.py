import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages

import asyncpg
from typing import List

from Utilities import Checks, Vars, AcolyteObject, PlayerObject

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
          ORDER BY xp DESC;
          """
    list_ids = await conn.fetch(psql, user_id)
    temp=[record['acolyte_id'] for record in list_ids]
    return [await AcolyteObject.get_acolyte_by_id(conn,id) for id in temp]

class Acolytes(commands.Cog):
    """
    All of the commands relating to Acolytes
    """
    def __init__(self,bot):
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
                    name=( 
                        f"({info['Rarity']}\u2B50) {info['Name']}: "
                        f"`{inv[start].acolyte_id}` [EQUIPPED]"),
                    value=( 
                        f"**Level:** {inv[start].level}, " 
                        f"**Attack:** {inv[start].get_attack()}, **Crit:** "
                        f"{inv[start].get_crit()}, **Dupes:** "
                        f"{inv[start].dupes}\n **Effect:** {info['Effect']}"),
                    inline=False)
            else:
                embed.add_field(
                    name=( 
                        f"({info['Rarity']}\u2B50) {info['Name']}: "
                        f"`{inv[start].acolyte_id}`"),
                    value=( 
                        f"**Level:** {inv[start].level}, " 
                        f"**Attack:** {inv[start].get_attack()}, "
                        f"**Crit:** {inv[start].get_crit()}, " 
                        f"**Dupes:** {inv[start].dupes}\n"
                        f"**Effect:** {info['Effect']}"),
                    inline=False)
            iteration += 1
            start += 1
        return embed

    @commands.slash_command()
    async def acolyte(self, ctx,
        name : Option(str, 
            description="The name of the acolyte you are viewing")):
        """View an acolyte's general information."""
        if name.lower() == "prxrdr":
            name = "PrxRdr"
        else:
            name = name.title()

        try:
            acolyte_info = AcolyteObject.Acolyte.get_acolyte_by_name(name)
        except KeyError:
            return await ctx.respond(
                f"There is no such acolyte with the name {name}."
            )
        
        embed = discord.Embed(            
                title=acolyte_info["Name"],
                color=Vars.ABLUE)

        embed.set_thumbnail(url=acolyte_info["Image"])
        embed.add_field(name="Backstory", value=acolyte_info["Story"])
        embed.add_field(
            name="Effect", 
            value=acolyte_info["Effect"], 
            inline=False)
        embed.add_field(name="Stats",
            value=(
                f"Attack: `{acolyte_info['Attack']}` \n "
                f"Crit: `{acolyte_info['Crit']}` \n"
                f"HP: `{acolyte_info['HP']}` \n "),
            inline=False)
        embed.add_field(name="Details",
            value=(
                f"Rarity: `{acolyte_info['Rarity']}`\u2B50\n"
                f"Upgrade Material: `{acolyte_info['Mat']}` \n"),
            inline=True)
        await ctx.respond(embed=embed)

    @commands.slash_command(guild_ids=[196465885148479489])
    @commands.check(Checks.is_player)
    async def tavern(self, ctx):
        """View a list of all your owned acolytes."""
        async with self.bot.db.acquire() as conn:
            acolytes= await get_all_acolytes(conn, ctx.author.id)
            player=await PlayerObject.get_player_by_id(conn, ctx.author.id)
            embeds = []
            for i in range(0, len(acolytes), 5): #list 5 entries at a time
                embeds.append(self.write(i, acolytes, player))
            if len(embeds) == 0:
                await ctx.reply('Your tavern is empty!')
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

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def train(self, ctx, 
            instance_id : Option(int, description="The acolyte's ID"), 
            iterations : Option(int,
                description="The amount of training sessions",
                min_value=1,
                max_value=100)):
        """Train your acolyte, spending gold and resources for xp."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if await player.is_acolyte_owner(conn,instance_id)==False:
                raise Checks.NotAcolyteOwner
            acolyte=await AcolyteObject.get_acolyte_by_id(conn,instance_id)
            acolyte_info=acolyte.gen_dict
            #you can not have an acolyte over level 100
            if acolyte.level >= 100:
                return await ctx.respond(
                    f"{acolyte_info['Name']} is already at maximum level!")
           
            mat=acolyte_info['Mat']
            #Make sure player has the resources and gold to train
            gold_needed=300*iterations
            mat_needed=75*iterations
            mat_dict=await player.get_backpack(conn)
            player_mat=mat_dict[mat]
            total_xp=5000*iterations

            if player_mat < mat_needed:
                raise Checks.NotEnoughResources(mat, mat_needed, player_mat)
            if player.gold < gold_needed:
                raise Checks.NotEnoughGold(gold_needed, player.gold)

            await ctx.respond((
                f"You trained with `{acolyte_info['Name']}`, " 
                f"consuming `{mat_needed}` {acolyte_info['Mat']} and" 
                f" `{gold_needed}` gold in the process. As a result," 
                f" `{acolyte_info['Name']}` gained {total_xp} exp!"))
            await acolyte.check_xp_increase(conn, ctx, total_xp)
            await player.give_gold(conn, gold_needed*-1)
            await player.give_resource(conn, mat, mat_needed*-1)

def setup(bot):
    bot.add_cog(Acolytes(bot))