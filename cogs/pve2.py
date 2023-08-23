import discord
from discord import Option, OptionChoice

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import asyncio
import random
import time

from Utilities import Checks, ItemObject, PlayerObject, Vars
from Utilities.Analytics import stringify_gains
from Utilities.AyeshaBot import Ayesha
from Utilities.Combat import Action, Belligerent, CombatEngine, Effects


class pve2(commands.Cog):
    def __init__(self, bot: Ayesha) -> None:
        self.bot = bot


    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvE2 is ready.")


    # COMMANDS
    @commands.slash_command()
    @commands.check(Checks.is_player)
    @cooldown(1, 15, BucketType.user)
    async def pve2(self, ctx: discord.ApplicationContext,
            level : Option(int,
                description="The difficulty level of your opponent",
                min_value=1),
            auto : Option(str,
                description=(
                    "Play interactive with buttons or simulate an automatic "
                    "battle for decreased rewards"),
                choices = [
                    OptionChoice("Play Interactively", "Y"),
                    OptionChoice("Play Auto (Decreased Rewards)", "N")],
                required = False,
                default = "Y")):
        """Fight an enemy for gold, xp, and items!"""
        # Create Belligerents
        async with self.bot.db.acquire() as conn:
            player = await Belligerent.CombatPlayer.from_id(conn, ctx.author.id)

        if level > player.player.pve_limit:
            return await ctx.respond(
                f"You cannot attempt this level yet! To challenge bosses past "
                f"level 25, you will have to beat each level sequentially. You "
                f"can currently challenge up to level {player.player.pve_limit}.")

        interaction = await ctx.respond("Loading battle...")
        boss = Belligerent.Boss(level)

        # Main Game Loop
        engine = CombatEngine.CombatEngine(player, boss)
        # while engine:
        #     break
        #     # Update information display

        #     # Get player action

        #     # Get boss action

        #     # Process turn and generate responses
        #     # results = engine.process_turn()

        # Process Game End; `results` will hold last turn info
        victor = engine.get_victor()
        if isinstance(victor, Belligerent.CombatPlayer):
            pass # Victory conditions
        else:
            pass # Loss condiitons

        # Create and send result embed
        fmt = " | ".join(str(x) for x in [player, boss, engine])
        await interaction.edit_original_message(content=fmt)

        
def setup(bot: Ayesha):
    bot.add_cog(pve2(bot))
