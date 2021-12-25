import discord
from discord.commands.commands import Option, SlashCommand

from discord.ext import commands

from Utilities import Checks, Vars, PlayerObject

class ConfirmButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10.0)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.grey)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        self.stop()

class Profile(commands.Cog):
    """Create a character and view your stats!"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Profile is ready.")

    # COMMANDS
    @commands.slash_command(
        aliases=["begin", "create", "play"], 
        guild_ids=[762118688567984151])
    @commands.check(Checks.not_player)
    async def start(self, ctx, 
            name: Option(str, description="Your character's name",
                         required=False, default=None)):
        """Start the game of Ayesha."""
        if not name:
            name = ctx.author.name
        if len(name) > 32:
            raise Checks.ExcessiveCharacterCount(limit=32)

        embed = discord.Embed(
            title="Start the game of Ayesha?",
            color=Vars.ABLUE)
        embed.add_field(
            name=f"Your Name: {name}",
            value=(f"You can customize your name by redoing this command with "
                   f"the `name` parameter filled!"))
        view = ConfirmButton()
        msg = await ctx.respond(embed=embed, view=view)
        await view.wait()
        if view.value is None:
            await ctx.respond("Timed out.")
        elif view.value:
            await PlayerObject.create_character(
                await self.bot.db.acquire(),
                ctx.author.id,
                name
            )
            await ctx.respond(f"Started the game: {name}")
        else:
            await ctx.respond(f"You cancelled :(")
        await msg.delete_original_message()


def setup(bot):
    bot.add_cog(Profile(bot))