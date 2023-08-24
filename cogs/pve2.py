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
        engine, results = CombatEngine.CombatEngine.initialize(player, boss)
        while engine:
            actor = engine.actor
            content = f"{player}, {boss}, {results}"
            view = None
            if actor.is_player:
                # Update information display
                view = Action.ActionView(ctx.author.id)
                await interaction.edit_original_message(
                    content=content,
                    view=view
                )

                await view.wait()
                if not view.choice:
                    return await ctx.respond(
                        f"You fled the battle as you ran out of time to move.")
                action = view.choice
            else:
                await interaction.edit_original_message(
                    content=content,
                    view=None
                )
                action = Action.Action.ATTACK
                await asyncio.sleep(3)  # If boss turn, let player read results

            # Process turn and generate responses
            results = engine.process_turn(action)

        # Process Game End; `results` will hold last turn info
        victor = engine.get_victor()
        if isinstance(victor, Belligerent.CombatPlayer):
            fmt = "win\n" # Victory conditions
        else:
            fmt = "loss\n" # Loss condiitons

        # Create and send result embed
        fmt += " | ".join(str(x) for x in [player, boss, results])
        await interaction.edit_original_message(content=fmt, view=None)

        
def setup(bot: Ayesha):
    bot.add_cog(pve2(bot))
