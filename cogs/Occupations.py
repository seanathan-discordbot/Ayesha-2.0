import discord
from discord import Option, OptionChoice

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from Utilities import Checks, PlayerObject, Vars
from Utilities.ConfirmationMenu import ConfirmationMenu

class OccupationMenu(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        # Exclude last entry; its the empty occupation (Name = None)
        options = [discord.SelectOption(label=o) for o in Vars.OCCUPATIONS][:-1]
        super().__init__(placeholder="Pick an Occupation", options=options)

    async def callback(self, interaction : discord.Interaction):
        if interaction.user.id != self.author.id:
            return
        
        occ = Vars.OCCUPATIONS[self.values[0]] # The dict for just this occ
        embed = discord.Embed(title=occ['Name'], description=occ['Desc'], 
            color=Vars.ABLUE)
        embed.add_field(name="Passive Effect", value=occ['Passive'])
        embed.add_field(name="Empowered Command", 
            value=occ['Command'])
        embed.add_field(
            name=(
                "Gain 20 ATK for having a weapon of one of these types "
                "equipped:"),
            value=", ".join(occ['weapon_bonus']),
            inline=False)
            
        await interaction.response.edit_message(embed=embed)

class OriginMenu(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        # Exclude last entry; its the empty origin
        options = [discord.SelectOption(label=o) for o in Vars.ORIGINS][:-1]
        super().__init__(placeholder="Pick something!", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return
        
        ori = Vars.ORIGINS[self.values[0]]
        embed = discord.Embed(
            title=ori['Name'], 
            description=(
                f"{ori['Desc']}\n\n"
                f"**Passive Effect:** {ori['Passive']}"))
        await interaction.response.edit_message(embed=embed)


class Occupations(commands.Cog):
    """Customize your character!"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Occupations is ready.")

    # COMMANDS
    @commands.slash_command()
    @commands.check(Checks.is_player)
    @cooldown(3, 259200, BucketType.user)
    async def lore(self, ctx, 
            setting : Option(str,
                description="The aspect of your profile to change",
                choices=[
                    OptionChoice("Change your Occupation", "Occ"),
                    OptionChoice("Change your Origin/Homeland", "Ori")])):
        """Choose your character's occupation or origin."""
        if setting == "Occ":
            # Create a menu of the occupations for player to choose
            view = ConfirmationMenu(ctx.author)
            menu = OccupationMenu(ctx.author)
            view.add_item(menu)
            embed = discord.Embed(title="Career Changing Menu")
            embed.set_image(url="https://i.imgur.com/hr4dLr7.jpeg")
            msg = await ctx.respond(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                await ctx.respond("Timed out.")
            elif view.value:
                try:
                    occ = menu.values[0]
                except IndexError: # pressed confirm on home page
                    await ctx.respond("Don't confirm the landing page.")
                else:
                    async with self.bot.db.acquire() as conn:
                        player = await PlayerObject.get_player_by_id(
                            conn, ctx.author.id)
                        await player.set_occupation(conn, occ)
                        await ctx.respond(f"You are now a **{occ}**!")
            else:
                await ctx.respond("You decided not to change your occupation.")
            await msg.delete_original_message()

        else:
            view = ConfirmationMenu(ctx.author)
            menu = OriginMenu(ctx.author)
            view.add_item(menu)
            embed = discord.Embed(title="Origin Changing Menu")
            embed.set_image(url="https://i.imgur.com/9hqOOTf.jpeg")
            msg = await ctx.respond(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                await ctx.respond("Timed out.")
            elif view.value:
                try:
                    ori = menu.values[0]
                except IndexError: # pressed confirm on home page
                    await ctx.respond("Don't confirm the landing page.")
                else:
                    async with self.bot.db.acquire() as conn:
                        player = await PlayerObject.get_player_by_id(
                            conn, ctx.author.id)
                        await player.set_origin(conn, ori)
                        await ctx.respond(f"Homeland set to **{ori}**!")
            else:
                await ctx.respond("You decided not to change your origin.")
            await msg.delete_original_message()


def setup(bot):
    bot.add_cog(Occupations(bot))