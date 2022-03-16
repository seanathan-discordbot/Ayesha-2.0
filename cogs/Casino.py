import discord
from discord import Option, OptionChoice

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import asyncio
import random

from Utilities import Checks, PlayerObject, Vars
from Utilities.ConfirmationMenu import OneButtonView

class Casino(commands.Cog):
    """Casino text"""

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Casino is ready.")

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def coinflip(self, ctx : discord.ApplicationContext, 
            call : Option(str,
                description="Bet on heads or tails",
                choices=[OptionChoice("Heads"), OptionChoice("Tails")],
                default="Heads"
            ),
            wager : Option(int, 
                description="The amount of gold you are betting (up to 25k)",
                min_value=1,
                max_value=25000,
                default=1000)):
        """Wager some money on a coinflip for the classic 50/50 gamble."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.gold < wager:
                raise Checks.NotEnoughGold(wager, player.gold)

            msg = f"The coin landed on **{call}**!"
            if random.choice(["Heads", "Tails"]) == call:
                await player.give_gold(conn, wager)
                await ctx.respond(f"{msg} You made `{wager}` gold.")
            else:
                await player.give_gold(conn, -wager)
                call = "Tails" if call == "Heads" else "Heads"
                await ctx.respond(
                    f"{msg} You lost your `{wager}` gold wager.")

    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    async def roulette(self, ctx : discord.ApplicationContext,
            bet_type : Option(str,
                description="The odds you want to play at",
                required=True,
                choices=[
                    OptionChoice(
                        "Straight-up: Bet on rolling a single number",
                        "Straight-up"),
                    OptionChoice(
                        ("Snake: Bet on rolling 1, 5, 9, 12, 14, 16, 19, 23, "
                         "27, 30, 32, or 34"),
                        "Snake"),
                    OptionChoice("Even: Bet on rolling an even number", "Even"),
                    OptionChoice("Odd: Bet on rolling an odd number", "Odd")]),
            bet_number : Option(int,
                description=(
                    "If you bet straight-up, call the number you think the "
                    "ball will land on"),
                default = 7,
                min_value=1,
                max_value=36),
            wager : Option(int,
                description="The amount of gold you are betting (up to 50k)",
                min_value=1,
                max_value=50000,
                default=1000)):
        """Play a game of Roulette"""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.gold < wager:
                raise Checks.NotEnoughGold(wager, player.gold)

            # Perform the roulette
            SNAKE = [1, 5, 9, 12, 14, 16, 19, 23, 27, 30, 32, 34]
            landing = random.randint(0, 36)
            msg = f"The ball landed on **{landing}**!"
            if landing == 0:
                await player.give_gold(conn, -wager//2)
                return await ctx.respond(f"{msg} You regained half your wager.")
            
            # Determine outcome based on bet type
            # Payouts taken from https://www.onlinegambling.com/casino/roulette/bets-payouts/
            if bet_type == "Straight-up" and bet_number == landing:
                await player.give_gold(conn, wager*35) # 35:1 stakes
                await ctx.respond(f"{msg} You made `{wager*35}` gold!")
            elif bet_type == "Snake" and landing in SNAKE:
                await player.give_gold(conn, wager*2)
                await ctx.respond(f"{msg} You made `{wager*2}` gold!")
            elif bet_type == "Even" and landing % 2 == 0:
                await player.give_gold(conn, wager)
                await ctx.respond(f"{msg} You made `{wager}` gold!")
            elif bet_type == "Odd" and landing % 2 == 1:
                await player.give_gold(conn, wager)
                await ctx.respond(f"{msg} You made `{wager}` gold!")
            else:
                await player.give_gold(conn, -wager)
                await ctx.respond(f"{msg} You lost your bet.")

    @commands.slash_command(guild_ids=[762118688567984151])
    @cooldown(1, 10, BucketType.user)
    @commands.check(Checks.is_player)
    async def craps(self, ctx : discord.ApplicationContext,
            wager : Option(int,
                description="The amount of gold you are betting (up to 100k)",
                min_value=1,
                max_value=100000,
                default=1000)):
        """Play a game of craps/seven-elevens on Pass Line rules."""
        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.gold < wager:
                raise Checks.NotEnoughGold(wager, player.gold)

            # Game is printed as an embed            
            display = discord.Embed(
                title=f"Craps: {ctx.author.display_name}", color=Vars.ABLUE)
            display.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url)
            display.add_field(
                name=f"Press Shoot! to roll the die!", 
                value=(f"Numbers to win: 7, 11\nNumbers to lose: 2, 3, 12"))

            # Create a button that will determine dice rolls
            view = OneButtonView("Shoot!", ctx.author, True, 15)
            interaction = await ctx.respond(embed=display, view=view)
            turn_counter = 1
            goal_number = 0
            die1, die2 = 0, 0
            victory, loss = False, False

            # Game loops until over
            while not victory and not loss:
                await view.wait()
                if view.value:
                    die1, die2 = random.randint(1, 6), random.randint(1, 6)
                    total = die1 + die2
                    if turn_counter == 1: 
                        if total in (7, 11): # win
                            victory = True
                        elif total in (2, 3, 12): # lose
                            loss = True
                        else: # goal_number becomes the number to repeat
                            goal_number = total
                    else:
                        if total == goal_number: # win
                            victory = True
                        elif total == 7: # lose
                            loss = True

                else: # Player didn't respond
                    await player.give_gold(conn, -wager)
                    msg = (
                        f"You left the game and forfeit your `{wager}` "
                        f"gold wager.")
                    await interaction.edit_original_message(view=None)
                    return await interaction.followup.send(msg) # end game here

                # Edit the message to reflect gameplay
                display.set_field_at(0, 
                    name=f"Press Shoot! to roll the die!",
                    value=(
                        f"You rolled a **{die1}** and a **{die2}**.\n\n"
                        f"Your Roll: **{total}**\n"
                        f"Number to Win: **{goal_number}**\n"
                        f"Number to Lose: **7**"))

                # View needs to be reloaded to be interactive again
                view = OneButtonView("Shoot!", ctx.author, True, 15)
                await interaction.edit_original_message(
                    embed=display, view=view)
                turn_counter += 1

            await interaction.edit_original_message(view=None)
            if victory:
                await player.give_gold(conn, wager)
                await interaction.followup.send(
                    f"You won and received `{wager}` gold!")
            else: # then loss
                await player.give_gold(conn, -wager)
                await interaction.followup.send((
                    f"You rolled a **{total}** and lost the game and your "
                    f"`{wager}` gold wager!"))

    @commands.slash_command(guild_ids=[762118688567984151])
    @cooldown(1, 10, BucketType.user)
    @commands.check(Checks.is_player)
    async def race(self, ctx : discord.ApplicationContext, 
            bet : Option(str,
                description="The animal you are betting on winning the race",
                required=True,
                choices=[
                    OptionChoice(c) for c in
                    ["Duck", "Swan", "Dog", "Horse", "Turtle", "Rabbit"]]), 
            wager : Option(int, 
                description="The amount of gold you are betting (up to 100k)",
                default=1000,
                min_value=1,
                max_value=100000)):
        """Bet on an animal race!"""
        names = ["Duck", "Swan", "Dog", "Horse", "Turtle", "Rabbit"]
        emojis = ["🦆", "🦢", "🐕", "🐎", "🐢", "🐇"]
        racers = {
            n : {
                "emoji" : e,
                "string" : "||" + "."*19 + e,
                "score" : 0,
                "player" : True if n == bet else False
            } for n, e in zip(names, emojis)}

        async with self.bot.db.acquire() as conn: # Remember to reconnect later
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if player.gold < wager:
                raise Checks.NotEnoughGold(wager, player.gold)

        # Race is printed on an embed
        output = "```" + "\n".join([racers[r]['string'] for r in racers]) +\
            "```"
        display = discord.Embed(
            title="And the race is on!", color=Vars.ABLUE, description=output)
        interaction = await ctx.respond(embed=display)

        # Game Loop - extraordinarily bad code even for my standards geez
        while max([racers[r]['score'] for r in racers]) <= 100:
            bet_str = ""
            for racer in racers:
                # Change their progress and accompanying data
                advance = random.randint(3, 14)
                racers[racer]['score'] += advance
                dots = racers[racer]['score'] // 5
                if dots >= 20: # They pass the finish line
                    racers[racer]['string'] = "|" + racers[racer]['emoji'] +\
                        "."*20
                else:
                    racers[racer]['string'] = "||" + "."*(19-dots) +\
                        racers[racer]['emoji'] + "."*(dots)

                # If racer is the bet, come up with some string
                if racer == bet:
                    e = racers[racer]['emoji']
                    if advance < 7:
                        bet_str = random.choice([
                            f"{e} falters!",
                            f"{e} has been outgunned!",
                            f"{e} trips!",
                            f"{e} was the sussy-impostor all along!",
                            f"{e} eats a fly and momentarily loses focus!"])
                    elif advance < 11:
                        bet_str = random.choice([
                            f"{e} keeps pace.",
                            f"{e} settles into mediocrity.",
                            f"{e} is showing signs of exhaustion.",
                            f"{e} passes a checkpoint!"])
                    else:
                        bet_str = random.choice([
                            f"{e} gains a quick burst of speed!",
                            f"{e} is one with nature.",
                            f"{e} is showing them who's boss!",
                            f"{e} leaps over an obstacle."])

            output = bet_str +"\n```" +\
                "\n".join([racers[r]['string'] for r in racers]) + "```"
            display = discord.Embed(
                title="And the race is on!", color=Vars.ABLUE, 
                description=output)
            await interaction.edit_original_message(embed=display)
            await asyncio.sleep(3)

        # Find the winner
        winners = [r for r in racers if racers[r]['score'] >= 100]
        win_str = ", ".join([racers[r]["emoji"] for r in winners])
        message = f"The winner(s) are {win_str}"

        async with self.bot.db.acquire() as conn:
            if bet in winners: # Then player's choice won
                payout = int(wager * 6.25 / len(winners)) # // gave float anyway
                await player.give_gold(conn, payout)
                message += f"\n You received a payout of `{payout}` gold!"
            else:
                await player.give_gold(conn, -wager)
                message +=f"\n You lost your bet and your `{wager}` gold wager!"
    
        await interaction.followup.send(message)


def setup(bot):
    bot.add_cog(Casino(bot))