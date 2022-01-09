import discord
from discord import player
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

import asyncio
import random

from Utilities import Checks, CombatObject, PlayerObject, Vars
from Utilities.CombatObject import CombatInstance
from Utilities.ConfirmationMenu import OfferMenu

class PvP(commands.Cog):
    """PvP Text"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvP is ready.")

    # AUXILIARY FUNCTIONS
    async def run_pvp(self, ctx, author : discord.Member, 
            opponent : discord.Member):
        """Runs the PvP instance."""
        if author.id == opponent.id:
            return await ctx.respond(
                f"You cannot challenge yourself.")

        # Ask for permission to perform PvP
        view = OfferMenu(author, opponent)
        interaction = await ctx.respond(
            content=(
                f"{opponent.mention}, {author.mention} is challenging you "
                f"to a battle! Do you accept?"),
            view=view)
        await view.wait()
        if view.value:
            pass
        else:
            return await interaction.edit_original_message(
                content="They declined.", view=None)

        # If they accept, load the players and create belligerents
        async with self.bot.db.acquire() as conn:
            initiator = await PlayerObject.get_player_by_id(conn, author.id)
            adversary = await PlayerObject.get_player_by_id(conn, opponent.id)
        player1 = CombatObject.Belligerent.load_player(initiator)
        player2 = CombatObject.Belligerent.load_player(adversary)

        # Main game loop, should be as close to PvE as possible
        # interaction = await ctx.respond("Loading battle...")
        turn_counter = 1
        recent_turns = [
            f"Battle begins between **{player1.name}** and **{player2.name}**."]
        while turn_counter <= 25:
            # Update information display
            embed = discord.Embed(
                title = f"Battle: {player1.name} vs. {player2.name}",
                color = Vars.ABLUE)
            embed.add_field(
                name=player1.name,
                value=(
                    f"ATK: `{player1.attack}` | CRIT: `{player1.crit}%`\n"
                    f"HP: `{player1.current_hp}` | DEF: `{player1.defense}%`"))
            embed.add_field(
                name=player2.name,
                value=(
                    f"ATK: `{player2.attack}` | CRIT: `{player2.crit}%`\n"
                    f"HP: `{player2.current_hp}` | DEF: `{player2.defense}%`"))
            log = ""
            for turn in recent_turns[-5:]:
                log += f"{turn}\n\n"
            embed.add_field(
                name="Battle Log",
                value=log,
                inline=False)

            await interaction.edit_original_message(
                content=None, embed=embed, view=None)

            # Determine belligerent actions
            player1.last_move = random.choices(
                population=["Attack", "Block", "Parry", "Heal", "Bide"],
                weights=[50, 20, 20, 3, 7])[0]
            player2.last_move = random.choices(
                population=["Attack", "Block", "Parry", "Heal", "Bide"],
                weights=[50, 20, 20, 3, 7])[0]

            # Calculate damage based off actions
            combat_turn = CombatInstance(player1, player2, turn_counter)
            recent_turns.append(combat_turn.get_turn_str())
            player1, player2 = combat_turn.apply_damage()

            # Check for victory
            if player1.current_hp <= 0 or player2.current_hp <= 0:
                break

            # Set up for next turn
            player1, player2 = CombatInstance.on_turn_end(player1, player2)

            turn_counter += 1
            await asyncio.sleep(3)

        # With loop over, determine winner and give rewards
        async with self.bot.db.acquire() as conn:
            if player1.current_hp > player2.current_hp:
                await initiator.log_pvp(conn, True)
                await adversary.log_pvp(conn, False)
                recent_turns.append(
                    f"**{author.mention} has proven their strength!**")
            elif player1.current_hp < player2.current_hp:
                await initiator.log_pvp(conn, False)
                await adversary.log_pvp(conn, True)
                recent_turns.append(
                    f"**{opponent.mention} has proven their strength!**")
            else:
                await initiator.log_pvp(conn, False)
                await adversary.log_pvp(conn, False)
                recent_turns.append(
                    f"**The battle has ended in a draw!**")

        log = ""
        for turn in recent_turns[-5:]:
            log += f"{turn}\n\n"
        embed.set_field_at(2, name="Battle Log", value=log, inline=False)
        await interaction.edit_original_message(embed=embed)

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @cooldown(1, 15, BucketType.user)
    async def pvp(self, ctx, opponent : Option(discord.Member,
            description="The person you are challenging to battle",
            converter=commands.MemberConverter())):
        """Challenge another player to battle you."""
        await self.run_pvp(ctx, ctx.author, opponent)

    @commands.user_command(name="Challenge to PvP", 
        guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @cooldown(1, 15, BucketType.user)
    async def other_pvp(self, ctx, member: discord.Member):
        await self.run_pvp(ctx, ctx.author, member)



def setup(bot):
    bot.add_cog(PvP(bot))