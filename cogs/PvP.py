import discord
from discord import Option

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import asyncio
import random

from Utilities import Checks, PlayerObject, Vars
from Utilities.Combat import Belligerent, CombatEngine, CombatTurn
from Utilities.ConfirmationMenu import ConfirmationMenu
from Utilities.AyeshaBot import Ayesha

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

    def __init__(self, bot : Ayesha):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvP is ready.")

    # AUXILIARY FUNCTIONS
    def create_embed(self,
            data: CombatTurn.CombatTurn,
            player1: Belligerent.CombatPlayer,
            player2: Belligerent.CombatPlayer,
            message: str = ""
    ) -> discord.Embed:
        """Create the PvP UI given the combatants and recent turn data."""
        # Update information display
        embed = discord.Embed(
            title = f"Battle: {player1.name} vs. {player2.name}",
            color = Vars.ABLUE)
        for p in (player1, player2):
            embed.add_field(
                name=p.name,
                value=(
                    f"ATK: `{p.attack}` | CRIT: `{p.crit_rate}%`\n"
                    f"HP: `{p.current_hp}` | DEF: `{p.defense}%`"))
        embed.add_field(
            name="Battle Log",
            value=data.description + (f'\n{message}' if message else message),
            inline=False)
        return embed

    async def run_pvp(self, 
            ctx: discord.ApplicationContext, 
            author : discord.Member, 
            opponent : discord.Member
    ):
        """Runs the PvP instance."""
        if author.id == opponent.id:
            return await ctx.respond(
                f"You cannot challenge yourself.")

        # Ask for permission to perform PvP
        view = ConfirmationMenu(user=opponent)
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
            player1 = await Belligerent.CombatPlayer.from_id(conn, author.id)
            player2 = await Belligerent.CombatPlayer.from_id(conn, opponent.id)

        # Main game loop, should be as close to PvE as possible
        # interaction = await ctx.respond("Loading battle...")
        engine, results = CombatEngine.CombatEngine.initialize(player1, player2)
        while engine:
            embed = self.create_embed(results, player1, player2)

            await interaction.edit_original_message(
                content=None, embed=embed, view=None)

            # Determine belligerent actions
            action = engine.recommend_action(engine.actor, results)[0]

            # Calculate damage based off actions
            results = engine.process_turn(action)
            await asyncio.sleep(3)

        # With loop over, determine winner and give rewards
        victor = engine.get_victor()
        loser = player2 if victor == player1 else player1
        async with self.bot.db.acquire() as conn:
            await victor.player.log_pvp(conn, True)
            await loser.player.log_pvp(conn, False)

        log = f"**{victor.name} has proven their strength!**"
        embed = self.create_embed(results, player1, player2, log)
        await interaction.edit_original_message(embed=embed)


    # COMMANDS
    @commands.slash_command()
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

    @commands.slash_command()
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