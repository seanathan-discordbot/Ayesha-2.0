import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

import asyncio
import random

from Utilities import Checks, CombatObject, PlayerObject, Vars
from Utilities.CombatObject import CombatInstance

class PvE(commands.Cog):
    """Association Text"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvE is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def pve(self, ctx,
            level : Option(int,
                description="The difficulty level of your opponent",
                min_value=1,
                max_value=25)):
        """Fight an enemy for gold, xp, and items!"""
        async with self.bot.db.acquire() as conn:
            author = await PlayerObject.get_player_by_id(conn, ctx.author.id)
        # Create belligerents
        player = CombatObject.Belligerent.load_player(player=author)
        boss = CombatObject.Belligerent.load_boss(difficulty=level)
        
        # Main game loop
        interaction = await ctx.respond("Loading battle...")
        turn_counter = 1
        # Stores string information to display to player
        recent_turns = [
            f"Battle begins between **{player.name}** and **{boss.name}**.",] 
        while turn_counter <= 50: # Manually broken if HP hits 0
            # Update information display
            embed = discord.Embed(
                title=f"{player.name} vs. {boss.name}",
                color=Vars.ABLUE)
            embed.add_field(name="Attack", value=player.attack)
            embed.add_field(name="Crit Rate", value=f"{player.crit}%")
            embed.add_field(name="HP", value=player.current_hp)
            embed.add_field(name="Defense", value=f"{player.defense}%")
            embed.add_field(
                name=f"Enemy HP: `{boss.current_hp}`",
                value=(
                    f"🗡️ Attack, \N{SHIELD} Block, \N{CROSSED SWORDS} "
                    f"Parry, \u2764 Heal, \u23F1 Bide"),
                inline=False)
            embed.add_field(
                name=f"Turn {turn_counter}", 
                value="\n".join(recent_turns[-5:]),
                inline=False)

            view = CombatObject.ActionChoice(author_id=ctx.author.id)
            # Remaking the view every time is a bit of a problem but results
            # in more readable code than having one view handle everything
            await interaction.edit_original_message(
                content=None, embed=embed, view=view)

            # Determine belligerent actions
            await view.wait()
            if view.choice is None:
                return await ctx.respond(
                    f"You fled the battle as you ran out of time to move.")

            player.last_move = view.choice
            boss.last_move = random.choice(["Attack", "Block", "Parry"])

            # Calculate damage based off actions
            combat_turn = CombatInstance(player, boss, turn_counter)
            recent_turns.append(combat_turn.get_turn_str())
            player, boss = combat_turn.apply_damage() # Apply to belligerents

            # Check for victory
            end_condition = boss.current_hp <= 0 or player.current_hp <= 0 
            if end_condition or turn_counter > 50:
                break

            # Set up for next turn
            player, boss = CombatInstance.on_turn_end(player, boss)

            turn_counter += 1

        # Determine why loop ended
        if boss.current_hp <= 0:
            # Win
            return await interaction.edit_original_message(
                content="You win.", embed=None, view=None)
        else: 
            # Loss
            return await interaction.edit_original_message(
                content="You lose.", embed=None, view=None)


def setup(bot):
    bot.add_cog(PvE(bot))