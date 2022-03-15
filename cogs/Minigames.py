import discord
from discord import Option, OptionChoice

from discord.ext import commands

import asyncio
import asyncpg
import random

from Utilities import ConfirmationMenu, Vars

# The dictionary used is words_alpha given here: https://github.com/dwyl/english-words

point_conversion = {'k' : 5}

for key in ['a', 'e', 'i', 'l', 'n', 'o', 'r', 's', 't', 'u']:
    point_conversion[key] = 1
for key in ['d', 'g']:
    point_conversion[key] = 2
for key in ['b', 'c', 'm', 'p']:
    point_conversion[key] = 3
for key in ['f', 'h', 'v', 'w', 'y']:
    point_conversion[key] = 4
for key in ['j', 'x']:
    point_conversion[key] = 8
for key in ['q', 'z']:
    point_conversion[key] = 10

alphabet = list("abcdefghijklmnopqrstuvwxyz")


class JoinMenu(discord.ui.View):
    """Ripped from PvP.py. Why can't I ever write general utility classes?"""
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
            f"{self.author.display_name}'s Word Chain Game."))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user not in self.players


class WordChain:
    """A word chain instance. Instantiate the class with the required 
    parameters and run the 'play' method to begin the game.

    Attributes
    ----------
    bot : discord.Bot 
        The bot
    ctx : discord.ApplicationContext
        The context of the class instantiation
    type : str
        The game mode type: Solo, Pubic, Lightning, or Scrabble
    conn : asyncpg.Connection
        A connection to the game's database
    char_freq : dict
        A dictionary containing the amount of words starting with each
        letter
    timeout : float
        The time in seconds a player has to answer
    players : List[int]
        A list containing all players by their Discord ID
    points : dict
        A dictionary containing each player and the points they have earned
        This is used for Scrabble Mode
    """
    def __init__(self, bot : discord.Bot, ctx : discord.ApplicationContext,
            type : str, conn : asyncpg.Connection, char_freq : dict):
        """
        Parameters
        ----------
        bot : discord.Bot 
            The bot
        ctx : discord.ApplicationContext
            The context of the class instantiation
        type : str
            The game mode type: Solo, Pubic, Lightning, or Scrabble
        conn : asyncpg.Connection
            A connection to the game's database
        char_freq : dict
            A dictionary containing the amount of words starting with each
            letter
        """
        self.bot = bot
        self.ctx = ctx
        self.type = type
        self.host = ctx.author
        self.conn = conn
        self.char_freq = char_freq

        # Useful information 
        self.timeout = 15.0 if self.type == "Lightning" else 30.0
        self.players = [self.host]
        self.points = {} # for scrabble mode
        self.mention_str = "".join([p.mention for p in self.players])

        # Very wordy game rules go here
        self.BASE_RULES = (
            f"**Welcome to Word Chain: {self.type}!** {self.mention_str}\n\n"
            f"Word Chain is the ultimate test of your vocabulary. Each player "
            f"must give a word that *begins* with the *last letter* of the "
            f"prior person's own word. Each player has **{int(self.timeout)} "
            f"seconds** to give a valid word.\nValid words are English, one "
            f"string, and have no punctuation. Players are eliminated when "
            f"they give an invalid word or time runs out.\n\n"
            f"**IMPORTANT NOTICE:** When giving a word, players MUST ping "
            f"{self.bot.user.mention} somewhere in the message so that it "
            f"will be read. The ping can go anywhere. The first non-ping "
            f"word will be submitted. If you forget to ping, the timer "
            f"will continue.")

        self.SCRABBLE_RULES = self.BASE_RULES + (
            f"In **Scrabble Mode**, each word you give will earn you a varying "
            f"amount of points depending on the rarity of letters used. Try to "
            f"come up with the longest word! Play continues until someone is "
            f"eliminated; the winner is the player with the most points. "
            f"Have fun! \n\n"
            f"__Example:__ happy --> your --> rig --> guy... and so on")

        self.MULTIPLAYER_RULES = self.BASE_RULES + (
            f"In **Public/Lightning** Mode, play continues until one person "
            f"remains. Have fun!\n\n"
            f"__Example:__ happy --> your --> rig --> guy... and so on")

    async def play(self):
        """Begins the game according to the specified type."""
        if self.type == "Solo":
            await self.play_solo()
        else:
            await self.play_public()

    async def check_validity(self, letter : str, word : str) -> bool:
        """Checks to see if the given word meets the following criteria:
        1. Word begins with the passed letter
        2. Word is in the dictionary database
        """
        if not word.startswith(letter):
            return False

        psql = """
                SELECT id
                FROM word_list
                WHERE word = $1;
                """
        return await self.conn.fetchval(psql, word) is not None

    def calc_scrabble_score(self, word : str) -> int:
        """Calculates the points a word earns by scrabble character rules."""
        return sum([point_conversion[c] for c in word])

    async def input_solo_game(self, score : int):
        """Input game entry into database."""
        psql = """
                INSERT INTO solo_wins (player, score)
                VALUES ($1, $2);
                """
        await self.conn.execute(psql, self.host.id, score)

    async def play_solo(self):
        """Begin a singleplayer word chain game."""
        # Set-up game
        used_words = {}
        next_letter = random.choice(alphabet)

        # Make sure player reads rules and agrees to start the game
        confirmation = ConfirmationMenu.ConfirmationMenu(self.host)
        interaction = await self.ctx.respond(self.BASE_RULES, view=confirmation)
        await confirmation.wait()
        if confirmation.value is None:
            return await interaction.edit_original_message(
                content="Timed out.", view=None)
        elif not confirmation.value:
            return await interaction.edit_original_message(
                content="Cancelled the game.", view=None)

        # Begin game loop
        first_turn = True
        while True:
            # Prompt user to give a word
            message = (
                f"{self.host.mention}, give me a word beginning "
                f"with **{next_letter}**!")
            if not first_turn:
                message = f"My Word: **{word}**\n\n" + message
            await interaction.followup.send(content=message)
            first_turn = False

            # Wait for a player to give a word
            def word_reader(message):
                return message.author == self.host and \
                    message.channel == self.ctx.channel
            
            word = None
            while word is None:
                try:
                    response = await self.bot.wait_for(
                        "message", timeout=self.timeout, check=word_reader)
                    resp_str = response.content.lower().split()
                    # Gets the first word that isn't the bot ping
                    for string in resp_str:
                        word = string
                        if not string.startswith("<@!"):
                            break
                    # Not pinging the bot will continue the game it seems
                except asyncio.TimeoutError:
                    score = len(used_words) // 2
                    message = f"Out of Time! | Score : {score}"
                    await interaction.followup.send(content=message)
                    return await self.input_solo_game(score)

            # Check for word validity
            # 1. It has not been used
            # 2. It is in the dictionary of words
            # 3. It begins with the last letter of the last word given
            try:
                if used_words[word] > 0: # Word repeated, end game
                    score = len(used_words) // 2
                    message = (
                        f"Word already used! | Score: "
                        f"{score}")
                    await interaction.followup.send(content=message)
                    return await self.input_solo_game(score)
                else:
                    used_words[word] += 1
            except KeyError: # Word not yet given
                used_words[word] = 1

            if not await self.check_validity(next_letter, word):
                score = len(used_words) // 2
                message = f"Invalid Word! | Score: {score}"
                await interaction.followup.send(content=message)
                return await self.input_solo_game(score)

            # Set up for next turn
            next_letter = word[-1]
            
            # Now bot selects a word
                # NB: You can find my qualms with this issue in the old version
                # https://github.com/seanathan-discordbot/Ayesha_Bot/blob/main/cogs/Minigames.py
                # Line 402 - I like this option as it seems to frontload the 
                # work onto bot startup and I can take full advantage of the
                # entire vocabulary this time. In fact, the query execution
                # time seems to have been reduced from 100 ms to < 40. 
            word_id = random.randint(1, self.char_freq[next_letter])
            psql = f"""
                    WITH valid_words AS (
                        SELECT ROW_NUMBER() OVER () AS rank, word
                        FROM word_list
                        WHERE word LIKE '{next_letter}%'
                    )
                    SELECT word 
                    FROM valid_words
                    WHERE rank = $1;
                    """
            word = await self.conn.fetchval(psql, word_id)

            try:
                if used_words[word] > 0:
                    score = len(used_words)+1 // 2
                    message = (
                        f"I tried **{word}** but it was already used!\n"
                        f"You win! | Score : {score}")
                    await interaction.followup.send(content=message)
                    return await self.input_solo_game(score)
                else:
                    used_words[word] += 1
            except KeyError:
                used_words[word] = 1
            
            next_letter = word[-1]

    async def end_game(self, interaction : discord.Interaction, 
            word_count : int):
        """Ends the game for a public match"""
        if self.type == "Scrabble":
            # Get the player(s) with the highest score
            winner1 = max(self.points, key = lambda k : self.points[k])
            highscore = self.points[winner1]
            winners = []
            point_pairs = []
            for player in self.points:
                if self.points[player] == highscore:
                    winners.append(player.mention)
                point_pairs.append(f"{player.mention} : {self.points[player]}")

            # Send endgame message
            win_msg = "The winner(s) are "
            win_msg += ''.join(winners)
            win_msg += f"! They scored **{highscore}** points!\n\n"
            win_msg += '\n'.join(point_pairs)
            win_msg += f"\nPlayers gave a collective {word_count} words."

            await interaction.followup.send(win_msg)

            # Input in database
            for player in self.players:
                psql = """
                        INSERT INTO scrabble_wins (player, score)
                        VALUES ($1, $2);
                        """
                await self.conn.execute(psql, player.id, self.points[player])

        else: # In public/lightning, only 1 person is left in the players list
            win_msg = (
                f"{self.players[0].mention} wins!\n"
                f"Players gave a collective {word_count} words.")

            await interaction.followup.send(win_msg)

            if self.type == "Public":
                # postgres literally falls apart if I try an upsert idk why
                psql = """SELECT id FROM public_wins WHERE player = $1"""
                in_db = await self.conn.fetchval(psql, self.players[0].id)
                if in_db is not None: 
                    psql = """
                            UPDATE public_wins
                            SET win_amount = win_amount + 1
                            WHERE player = $1
                            """
                    await self.conn.execute(psql, self.players[0].id)
                else:
                    psql = """
                            INSERT INTO public_wins (player)
                            VALUES ($1)
                            """
                    await self.conn.execute(psql, self.players[0].id)
            else:
                psql = """SELECT id FROM lightning_wins WHERE player = $1"""
                in_db = await self.conn.fetchval(psql, self.players[0].id)
                if in_db is not None: 
                    psql = """
                            UPDATE lightning_wins
                            SET win_amount = win_amount + 1
                            WHERE player = $1
                            """
                    await self.conn.execute(psql, self.players[0].id)
                else:
                    psql = """
                            INSERT INTO lightning_wins (player)
                            VALUES ($1)
                            """
                    await self.conn.execute(psql, self.players[0].id)


    async def play_public(self):
        """Begin a multiplayer Word Chain game"""
        # Let player's join game
        join_menu = JoinMenu(self.host)
        join_msg = (
            f"{self.host.mention} has begun a game of **Word Chain: "
            f"{self.type}**\n Press the button below to join!")
        interaction = await self.ctx.respond(join_msg, view=join_menu)
        await join_menu.wait()
        await interaction.edit_original_message(view=None)
        if len(join_menu.players) < 2:
            return await interaction.followup.send("Not enough players joined.")
        self.players = join_menu.players

        # Set up game
        word = None
        used_words = {}
        next_letter = random.choice(alphabet)
        points = 0 # Points a word earns in Scrabble Mode
        eliminated = False

        # Read rules and start game
        if self.type == "Scrabble":
            await interaction.followup.send(self.SCRABBLE_RULES)
            self.points = {player : 0 for player in self.players}
        else:
            await interaction.followup.send(self.SCRABBLE_RULES)
        await asyncio.sleep(10)

        # Begin game loop
        # Game cycles through players by popping and re-appending them
        # Whoever is at the front of the list is taking their turn
        while len(self.players) > 1: # Scrabble mode will break loop itself
            # Prompt the next player to give a word
            prompt = (
                f"{self.players[0].mention}, give me a word beginning with "
                f"**{next_letter}!**")
            if len(used_words) > 0 and self.type == "Scrabble":
                prompt = f"**{word}** was worth **{points}** points!\n" + prompt
            await interaction.followup.send(prompt)

            # Wait for player to give a word
            def word_reader(message : discord.Message):
                return message.author == self.players[0] and \
                    message.channel == self.ctx.channel
            
            word = None
            while word is None:
                try:
                    response = await self.bot.wait_for(
                        "message", timeout=self.timeout, check=word_reader)
                    resp_str = response.content.lower().split()
                    # Gets the first word that isn't the bot ping
                    for string in resp_str:
                        word = string
                        if not string.startswith("<@!"):
                            break
                    # Not pinging the bot will continue the game it seems
                except asyncio.TimeoutError:
                    await interaction.followup.send(
                        "Out of time! | You have been eliminated.")
                    if self.type == "Scrabble":
                        return await self.end_game(interaction, len(used_words))
                    self.players.pop(0)
                    eliminated = True
                    break

            # Check for word validity
            # 1. It has not been used
            # 2. It is in the dictionary of words
            # 3. It begins with the last letter of the last word given
            if word in used_words: # I think this should be O(1)
                await interaction.followup.send(
                    f"This word was used by {used_words[word]}! | You have "
                    f"been eliminated.")
                if self.type == "Scrabble":
                    return await self.end_game(interaction, len(used_words))
                self.players.pop(0)
                eliminated = True

            if not await self.check_validity(next_letter, word):
                await interaction.followup.send(
                    "Invalid word! | You have been eliminated.")
                if self.type == "Scrabble":
                    return await self.end_game(interaction, len(used_words))
                self.players.pop(0)
                eliminated = True

            # Word passed check, calculate points, set up for next turn
            if self.type == "Scrabble":
                points = self.calc_scrabble_score(word)
                self.points[self.players[0]] += points
            if not eliminated:
                next_letter = word[-1]
                used_words[word] = self.players[0].mention
                self.players.append(self.players.pop(0))
            eliminated = False

        await self.end_game(interaction, len(used_words))


            


class Minigames(commands.Cog):
    """Minigames text"""

    def __init__(self,bot):
        self.bot = bot
        self.active_channels = {} # Prevent multiple games in one channel
    
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        # Get the amount of words that start with each letter
        async with self.bot.dictionary.acquire() as conn:
            letter_frequency = {}
            for letter in alphabet:
                psql = f"""
                        WITH ranks AS (
                            SELECT ROW_NUMBER() OVER () AS rank, word
                            FROM word_list
                            WHERE word LIKE '{letter}%'
                        )
                        SELECT COUNT(*) FROM ranks LIMIT 10;
                        """
                letter_frequency[letter] = await conn.fetchval(psql)
            self.letter_frequency = letter_frequency
        print("Minigames is ready.")

    # Commands
    @commands.slash_command(guild_ids=[762118688567984151])
    async def wordchain(self, ctx : discord.ApplicationContext, 
            mode : Option(str,
                description = "The Word Chain game mode you wish to play",
                required = True,
                choices = [
                    OptionChoice("Solo"),
                    OptionChoice("Public"),
                    OptionChoice("Lightning"),
                    OptionChoice("Scrabble")])):
        """Play a game of Word Chain - the vocabulary testing game!"""
        if ctx.channel.id in self.active_channels:
            return await ctx.respond((
                "There is already a game in this channel. Please wait for "
                "it to end or go to another channel."))
        self.active_channels[ctx.channel.id] = 1
        async with self.bot.dictionary.acquire() as conn:
            game = WordChain(self.bot, ctx, mode, conn, self.letter_frequency)
            await game.play()
        self.active_channels.pop(ctx.channel.id)



def setup(bot):
    bot.add_cog(Minigames(bot))