import discord
from discord import Option

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import asyncio
import random

from Utilities import Checks, CombatObject, PlayerObject, Vars
from Utilities.CombatObject import Belligerent, CombatInstance
from Utilities.ConfirmationMenu import OfferMenu

class JoinMenu(discord.ui.View):
    def __init__(self, author : discord.Member):
        self.author = author
        super().__init__(timeout=30.0)
        self.players = [author]

    @discord.ui.button(label="Join!", style=discord.ButtonStyle.primary)
    async def join(self, button : discord.ui.Button,
            interaction : discord.Interaction):
        self.players.append(interaction.user)
        await interaction.response.send_message((
            f"{interaction.user.mention} has joined "
            f"{self.author.display_name}'s tournament."))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user not in self.players

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
        )
    @commands.check(Checks.is_player)
    @cooldown(1, 15, BucketType.user)
    async def other_pvp(self, ctx, member: discord.Member):
        await self.run_pvp(ctx, ctx.author, member)

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @cooldown(1, 120, BucketType.channel)
    async def tournament(self, ctx):
        """Start a single-elimination PvP tournament!"""
        def match_players(players : list):
            """Matches the players in the inputted list.
            Returns a list of tuples, each tuple holding the info for 2 players.
            If there are an odd amount of players, the remainder gets matched against a PvE boss ;).
            """
            matches = []
            i = 0
            while i < len(players):
                players[i]["Belligerent"] = Belligerent.load_player(players[i]["Player"])
                try:
                    players[i+1]["Belligerent"] = Belligerent.load_player(players[i+1]["Player"])
                except KeyError: #In case there are an odd amount of players
                    pass
                finally:
                    match = (
                        players[i],
                        players[i+1]
                    )
                    matches.append(match)
                    i+=2 #Skip over every other player since matches have 2
                    
            return matches      

        def simulate_battle(player1 : dict, player2 : dict):
            """Simulate a battle between two players based off all stats.
            Each side has a chance to land a "crit" (based off crit) and win.
            Otherwise it will base the victor off the proportions of the attack.
            Return the winner and loser in that order."""
            # See if one side lands a critical hit
            player1["Belligerent"].crit *= 2
            player1["Belligerent"].crit -= player2["Belligerent"].defense

            player2["Belligerent"].crit *= 2
            player2["Belligerent"].crit -= player1["Belligerent"].defense
            player2["Belligerent"].crit += player1["Belligerent"].crit

            random_crit = random.randint(0, 1000)
            if random_crit < player1["Belligerent"].crit:
                return player1, player2
            elif random_crit < player2["Belligerent"].crit:
                return player2, player1
            
            # Weigh the sum of each player's stats
            p1 = player1["Belligerent"].attack * 4 \
                + player1["Belligerent"].crit * 8 \
                + player1["Belligerent"].defense * 9 \
                + player1["Belligerent"].max_hp
            p2 = player2["Belligerent"].attack * 4 \
                + player2["Belligerent"].crit * 8 \
                + player2["Belligerent"].defense * 9 \
                + player2["Belligerent"].max_hp

            victory_number = random.randint(0, p1 + p2)
            if victory_number < p1:
                return player1, player2
            else:
                return player2, player1

        # Prompt people to join the rounament
        view = JoinMenu(ctx.author)
        interaction = await ctx.respond(content="Join Tournament", view=view)
        await view.wait()
        await interaction.edit_original_message(view=None)

        # Parse the people who joined the tournament
        if len(view.players) < 2:
            ctx.command.reset_cooldown(ctx)
            return await interaction.followup.send(
                "Not enough people joined the tournament.")

        async with self.bot.db.acquire() as conn:
            players = [] # List of dicts containing User, Player, Belligerent
            for user in view.players:
                try:
                    player = await PlayerObject.get_player_by_id(conn, user.id)
                    p_dict = { # These dicts are bloated  
                        "User" : user, # Should be removed
                        "Player" : player,
                        "Belligerent" : None
                    }
                    players.append(p_dict)
                except Checks.PlayerHasNoChar:
                    continue

            # Add fake players until some number 2^n is hit
            n = 1
            while 2**n < len(players):
                n += 1
            while len(players) < 2**n:
                boss_level = random.randint(1, 14)
                fake_player = {
                    "Belligerent" : Belligerent.load_boss(boss_level)
                }
                players.append(fake_player)

        await interaction.followup.send(
            f"Tournament hosted by {ctx.author.mention} starting with "
            f"{len(players)} participants!")

        # Iterate over players repeatedly, simulating battles and popping losers
        round_num = 1
        while len(players) > 1:
            await asyncio.sleep(3)

            round_msg = await ctx.followup.send((
                f"__**{ctx.author.mention}'s Tournament: Round "
                f"{round_num}**__\nPerforming battles..."))

            matches = match_players(players) # Divide players into pairs
            round_output = [] # Stores results of each battle

            for match in matches:
                # Simulate battle and determine winner
                winner, loser = simulate_battle(match[0], match[1])

                # Append result and eliminate loser
                verbs = ["defeated","vanquished","knocked out","eliminated",
                    "sussy-amogused"]
                output = (
                    f"**{winner['Belligerent'].name}** has "
                    f"{random.choice(verbs)} **{loser['Belligerent'].name}**.")
                round_output.append(output)
                try:
                    players.remove(loser)
                except ValueError:
                    pass
            
            embed = discord.Embed(
                title=f"Round {round_num}",
                description="\n".join(round_output),
                color=Vars.ABLUE)
            await round_msg.edit(content=None, embed=embed)
            round_num += 1

        ctx.command.reset_cooldown(ctx)
        try:
            await interaction.followup.send(
                f"The winner of the tournament is "
                f"{players[0]['User'].mention}!")
        except KeyError:
            await interaction.followup.send(
                f"Y'all lost to an NPC bruh")


def setup(bot):
    bot.add_cog(PvP(bot))