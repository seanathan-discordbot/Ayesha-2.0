import discord
from discord import Option, OptionChoice

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import asyncio
from typing import Iterable

from Utilities import Checks, Vars
from Utilities.AyeshaBot import Ayesha
from Utilities.Combat import Action, Belligerent, CombatEngine


class pve2(commands.Cog):
    def __init__(self, bot: Ayesha) -> None:
        self.bot = bot


    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvE2 is ready.")

    # AUXILIARY FUNCTIONS
    def list2str(self, arr: Iterable):
        return " ".join(str(x) for x in arr)

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
            view = None
            
            embed = discord.Embed(
                title=f"{player.name} vs. {boss.name} (Level {level})",
                color=Vars.ABLUE
            )
            embed.set_thumbnail(url="https://i.imgur.com/d7srIjy.png")
            embed.add_field(name="Attack", value=player.attack)
            embed.add_field(
                name="Crit Rate/Damage", 
                value=f"{player.crit_rate}%/+{player.crit_damage}%"
            )
            embed.add_field(
                name="HP",
                value=f"{player.current_hp}/{player.max_hp}"
            )
            embed.add_field(name="Defense", value=f"{player.defense}%")
            embed.add_field(name="Speed", value=player.speed)
            embed.add_field(name="DEF Pen", value=player.armor_pen)
            embed.add_field(
                name=f"Enemy HP: `{boss.current_hp}`   {self.list2str(boss.status)}",
                value=(
                    f"🗡️ Attack, \N{SHIELD} Block, \N{CROSSED SWORDS} "
                    f"Parry, \u2764 Heal, \u23F1 Bide"),
                inline=False)
            embed.add_field(
                name=f"Turn {results.turn}   {self.list2str(player.status)}", 
                value=results.description,
                inline=False)

            if actor.is_player:
                # Update information display
                view = Action.ActionView(ctx.author.id)
                await interaction.edit_original_message(
                    content=None,
                    embed=embed,
                    view=view
                )

                await view.wait()
                if not view.choice:
                    return await ctx.respond(
                        f"You fled the battle as you ran out of time to move.")
                action = view.choice
            else:
                await interaction.edit_original_message(
                    content=None,
                    embed=embed,
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
