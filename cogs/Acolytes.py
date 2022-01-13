import discord
from discord.commands.commands import Option
import asyncpg
from discord.ext import commands, pages
from discord.ext.commands import converter
from discord.commands.commands import Option, OptionChoice
from Utilities import Checks, Vars, Analytics, AcolyteObject,PlayerObject

async def acolyte_equipped(player,acolyte_id):
    id_1=player.acolyte1.acolyte_id
    id_2=player.acolyte2.acolyte_id
    return (acolyte_id==id_1 or acolyte_id==id_2)

async def get_all_acolytes(conn : asyncpg.Connection, user_id : int):
    """Returns a list of 'AcolyteObject.Acolyte's the player with the ID owns"""
    psql = """
          SELECT acolyte_id
          FROM acolytes
          WHERE user_id = $1;
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
    async def write(self, start, inv, player,conn):
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
            if(await acolyte_equipped(player,inv[start].acolyte_id)):
                embed.add_field(name =( 
                    f"{info['Rarity']}\u2B50) {info['Name']} {inv[start].acolyte_id}"),
                    value =( 
                    f"**Level:** {inv[start].level}," 
                    f" **Attack:** {info['Attack']}, **Crit:** {info['Crit']}," 
                    f" **Dupes:** {inv[start].dupes}\n**Effect:** {info['Effect']}"
                    ),inline=False
                )
            iteration += 1
            start += 1
        return embed

    @commands.slash_command(guild_ids=[762118688567984151])
    async def acolye(self,ctx,
    name : Option(str, description="Enter the name of an acolyte to view it")):
        acolyte_info=AcolyteObject.get_acolyte_by_name(name)
        print("Creating embed")

        embed = discord.Embed(            
                title=acolyte_info["Name"],
                color=Vars.ABLUE
        )

        embed.set_thumbnail(url=acolyte_info["Image"])
        embed.add_field(name="Backstory",value=acolyte_info["Story"]+"")
        embed.add_field(name="Effect",value=acolyte_info["Effect"]+"")
        embed.add_field(name="Stats",
        value=(
            f"Attack: `{acolyte_info['Attack']}` \n "
            f"Crit: `{acolyte_info['Crit']}` \n"
            f"HP: `{acolyte_info['HP']}` \n "
        ),inline=True)
        embed.add_field(name="Details",
        value=(
            f"Rarity: `{acolyte_info['Rarity']}`\u2B50\n"
            f"Upgrade Material: `{acolyte_info['Mat']}` \n"
        ),inline=True)
        await ctx.respond(embed=embed)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.HasChar)
    async def tavern(self,ctx):
        user_id=ctx.author.id
        async with self.bot.db.acquire() as conn:
            acolytes= await get_all_acolytes(conn,user_id)
            player=await PlayerObject.get_player_by_id(conn,user_id)
            name=player.char_name
            embeds = []
            for i in range(0, len(acolytes), 5): #list 5 entries at a time
                embeds.append(await self.write(i,acolytes,player,conn)) 
                # Write will create the embeds
            if len(embeds) == 0:
                await ctx.reply('Your tavern is empty!')
            else:
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
    async def recruit(self,ctx,
    slot : Option(int, description="The slot you want to add the acolyte to",
    choices = [OptionChoice(name="Slot 1", value=1),OptionChoice(name="Slot 2", value=2)]),
    instance_id : Option(int, description="Id of acolyte to add to slot",
    required=False)):

        user_id=ctx.author.id
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            """
            if the user does not provide an acolyte id 
            unequip the acolyte in that slot
            """
            if(instance_id is None):
                await player.unequip_acolyte(conn,slot)
                await ctx.respond("Unequipped")

            owned = await player.is_acolyte_owner(conn,instance_id)
            if(owned == False):
                await ctx.respond('This acolyte isn\'t in your tavern.')

            if(player.acolyte1 is not None):
               await  player.unequip_acolyte(conn,slot)

            await player.equip_acolyte(conn,instance_id,slot)
            await ctx.respond("Eqipped")

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.HasChar)
    async def train (self,ctx,instance_id : Option(int,description="The acolytes' id"), 
    iterations : Option(int,description="The number of times you want to train your acolyte",min_value=1)):
        user_id= ctx.author.id
        """ 
        you can not run the upgrade command 
        on an acolyte for less than one iteration 
        """
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn,user_id)

            """
            the user can not upgrade an acolyte that is not theirs 
            so an error should be sent
            """ 
            if(await player.is_acolyte_owner(conn,instance_id)==False):
                await ctx.respond('This acolyte isn\'t in your tavern.')
            acolyte=await AcolyteObject.get_acolyte_by_id(conn,instance_id)
            acolyte_info=acolyte.gen_dict
            #you can not have an acolyte over level 100
            if acolyte.level >= 100:
                await ctx.reply(
                    f"{acolyte_info['Name']} is already at maximum level!")
           
            mat=acolyte_info['Mat']
            #Make sure player has the resources and gold to train
            #5000 xp = 50 of the mat + 250 gold
            gold_needed=250*iterations
            mat_needed=50*iterations
            player_gold=player.gold
            mat_dict=await player.get_backpack(conn)
            player_mat=mat_dict[mat]
            total_xp=5000*iterations

            if player_mat < mat_needed or player_gold < gold_needed:
                await ctx.respond((
                f"Training your acolyte costs `{mat_needed}`" 
                f"{acolyte_info['Mat']} and `{gold_needed}`gold." 
                f"You don\'t have enough resources to train."
                ))
            acolyte.check_xp_increase(total_xp)
            player.give_gold(conn,-(gold_needed))
            player.give_resource(conn,mat,-(mat_needed))
            await ctx.respond((
                f"You trained with `{acolyte_info['Name']}`" 
                f"consuming `{mat_needed}` {acolyte_info['Mat']} and" 
                f" `{gold_needed}` gold in the process. As a result," 
                f" `{acolyte_info['Name']}` gained {total_xp} exp!"))

def setup(bot):
    bot.add_cog(Acolytes(bot))