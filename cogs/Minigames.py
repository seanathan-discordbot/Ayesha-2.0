import discord
from discord import Option, OptionChoice

from discord.ext import commands

import asyncio
import asyncpg
import random

from Utilities import ConfirmationMenu, Vars
from Utilities.AyeshaBot import Ayesha

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
        if interaction.user not in self.players:
            return True
        else:
            await interaction.response.send_message(
                "You already joined!", ephemeral=True)
            return False


class LeaderboardMenu(discord.ui.Select):
    def __init__(self, author : discord.Member, embeds : dict):
        self.author = author
        self.embeds = embeds
        # Exclude last entry; its the empty occupation (Name = None)
        options = [
            discord.SelectOption(label="Most words in Solo", value="Solo"),
            discord.SelectOption(label="Highest points in Scrabble", 
                value="Scrabble")
        ]
        super().__init__(placeholder="View Leaderboards", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.embeds[self.values[0]])

    async def interaction_check(self, 
            interaction : discord.Interaction) -> bool:
        return interaction.user.id == self.author.id


class WordChain:
    """A word chain instance. Instantiate the class with the required 
    parameters and run the 'play' method to begin the game.

    Attributes
    ----------
    bot : discord.Bot 
        The bot
    ctx : discord.Message
        The original message that prompted this game
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
    def __init__(self, bot : Ayesha, ctx : discord.Message,
            type : str, conn : asyncpg.Connection, char_freq : dict):
        """
        Parameters
        ----------
        bot : discord.Bot 
            The bot
        ctx : discord.Message
            The original message that prompted this game
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
            f"\n\nIn **Scrabble Mode**, each word you give will earn you a "
            f"varying amount of points depending on the rarity of letters "
            f"used. Try to come up with the longest word! Play continues "
            f"until someone is eliminated; the winner is the player with the "
            f"most points. Have fun! \n\n"
            f"__Example:__ happy --> your --> rig --> guy... and so on")

        self.MULTIPLAYER_RULES = self.BASE_RULES + (
            f"\n\nIn **Public/Lightning** Mode, play continues until one "
            f"person remains. Have fun!\n\n"
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
                INSERT INTO solo_wins (player, score, player_name)
                VALUES ($1, $2, $3);
                """
        await self.conn.execute(psql, self.host.id, score, 
            self.players[0].name)

    async def play_solo(self):
        """Begin a singleplayer word chain game."""
        # Set-up game
        used_words = {}
        next_letter = random.choice(alphabet)

        # Make sure player reads rules and agrees to start the game
        confirmation = ConfirmationMenu.ConfirmationMenu(user=self.host, timeout=30.0)
        interaction = await self.ctx.reply(self.BASE_RULES, view=confirmation)
        await confirmation.wait()
        if confirmation.value is None:
            return await interaction.edit(content="Timed out.", view=None)
        elif not confirmation.value:
            return await interaction.edit(content="Cancelled the game.", view=None)
        else:
            await interaction.edit(view=None)

        # Begin game loop
        first_turn = True
        while True:
            # Prompt user to give a word
            message = (
                f"{self.host.mention}, give me a word beginning "
                f"with **{next_letter}**! (beta)")
            if not first_turn:
                message = f"My Word: **{word}**\n\n" + message
            await interaction.reply(content=message)
            first_turn = False

            # Wait for a player to give a word
            def word_reader(message : discord.Message):
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
                        if not string.startswith("<@"):
                            break
                    # Not pinging the bot will continue the game it seems
                except asyncio.TimeoutError:
                    score = len(used_words) // 2
                    message = f"Out of Time! | Score : {score}"
                    await interaction.reply(content=message)
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
                    await interaction.reply(content=message)
                    return await self.input_solo_game(score)
                else:
                    used_words[word] += 1
            except KeyError: # Word not yet given
                used_words[word] = 1

            if not await self.check_validity(next_letter, word):
                score = len(used_words) // 2
                message = f"Invalid Word! | Score: {score}"
                await interaction.reply(content=message)
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
                    await interaction.reply(content=message)
                    return await self.input_solo_game(score)
                else:
                    used_words[word] += 1
            except KeyError:
                used_words[word] = 1
            
            next_letter = word[-1]

    async def end_game(self, interaction : discord.Message, 
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

            await interaction.reply(win_msg)

            # Input in database
            for player in self.players:
                psql = """
                        INSERT INTO scrabble_wins (player, score, player_name)
                        VALUES ($1, $2, $3);
                        """
                await self.conn.execute(psql, player.id, self.points[player], 
                    player.name)

        else: # In public/lightning, only 1 person is left in the players list
            win_msg = (
                f"{self.players[0].mention} wins!\n"
                f"Players gave a collective {word_count} words.")

            await interaction.reply(win_msg)

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
                            INSERT INTO public_wins (player, player_name)
                            VALUES ($1, $2)
                            """
                    await self.conn.execute(psql, self.players[0].id, 
                        self.players[0].name)
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
                            INSERT INTO lightning_wins (player, player_name)
                            VALUES ($1, $2)
                            """
                    await self.conn.execute(psql, self.players[0].id, 
                        self.players[0].name)


    async def play_public(self):
        """Begin a multiplayer Word Chain game"""
        # Let player's join game
        join_menu = JoinMenu(self.host)
        join_msg = (
            f"{self.host.mention} has begun a game of **Word Chain: "
            f"{self.type}**\n Press the button below to join!")
        interaction = await self.ctx.reply(join_msg, view=join_menu)
        await join_menu.wait()
        await interaction.edit(view=None)
        if len(join_menu.players) < 2:
            return await interaction.reply("Not enough players joined.")
        self.players = join_menu.players

        # Set up game
        word = None
        used_words = {}
        next_letter = random.choice(alphabet)
        points = 0 # Points a word earns in Scrabble Mode
        eliminated = False

        # Read rules and start game
        if self.type == "Scrabble":
            await interaction.reply(self.SCRABBLE_RULES)
            self.points = {player : 0 for player in self.players}
        else:
            await interaction.reply(self.MULTIPLAYER_RULES)
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
            await interaction.reply(prompt)

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
                        if not string.startswith("<@"):
                            break
                    # Not pinging the bot will continue the game it seems
                except asyncio.TimeoutError:
                    await interaction.reply(
                        "Out of time! | You have been eliminated.")
                    if self.type == "Scrabble":
                        return await self.end_game(interaction, len(used_words))
                    self.players.pop(0)
                    eliminated = True
                    break
            
            if eliminated:
                continue

            # Check for word validity
            # 1. It has not been used
            # 2. It is in the dictionary of words
            # 3. It begins with the last letter of the last word given
            if word in used_words: # I think this should be O(1)
                await interaction.reply(
                    f"This word was used by {used_words[word]}! | You have "
                    f"been eliminated.")
                if self.type == "Scrabble":
                    return await self.end_game(interaction, len(used_words))
                self.players.pop(0)
                eliminated = True

            if not await self.check_validity(next_letter, word):
                await interaction.reply(
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

    def __init__(self, bot : Ayesha):
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

    @commands.Cog.listener()
    async def on_message(self, message : discord.Message):
        if message.author.bot:
            return

        solo = r"wordchain play solo" in message.content
        public = r"wordchain play public" in message.content
        lightning = r"wordchain play lightning" in message.content
        scrabble = r"wordchain play scrabble" in message.content

        if solo or public or lightning or scrabble:
            if message.channel.id in self.active_channels:
                return await message.reply((
                    "There is already a game in this channel. Please wait for "
                    "it to end or go to another channel."))
            self.active_channels[message.channel.id] = 1

            if solo:
                mode = "Solo"
            elif public:
                mode = "Public"
            elif lightning:
                mode = "Lightning"
            else:
                mode = "Scrabble"

            async with self.bot.dictionary.acquire() as conn:
                game = WordChain(self.bot, message, mode, conn, self.letter_frequency)
                await game.play()

            self.active_channels.pop(message.channel.id)


    # AUXILIARY FUNCTIONS
    def format_leaderboard(self, lb, author_name : str, author_rank : int, 
            author_val : int) -> str:
        """Returns a formatted block of text showing the leaderboard.
        lb must be an asyncpg.Record or list. 
        """
        # Make all the names equal width
        names = [record['player_name'] for record in lb]
        names.append(author_name)
        name_length = len(max(names, key=len))
        names = [name + " "*(name_length - len(name)) for name in names]

        ranks = []
        for i, record in enumerate(lb):
            if i+1 < 10: # Make all ranks equal width
                j = "0"+str(i+1)
            else:
                j = "10"
            ranks.append(f"{j} | {names[i]} | {record['score']}")
            
        if author_rank < 10:
            author_rank = "0" + str(author_rank)

        return "```" + "\n".join(ranks) + (
            f"\n{'-'*len(max(ranks, key=len))}\n"
            f"{author_rank} | {names[-1]} | {author_val}```")

    # Commands
    w = discord.commands.SlashCommandGroup("wordchain", 
        "Commands related to Word Chain")

    @w.command()
    async def play(self, ctx : discord.ApplicationContext):
        """Play a game of Word Chain - the vocabulary testing game!"""
        ping = f"<@{self.bot.user.id}>"
        return await ctx.respond((
            "Since normal slash commands have a time limit of 15 minutes, and "
            "some games have exceeded that limit, WordChain has been migrated "
            "back to a class-style prefixed command. To begin a WordChain "
            "game, please copy and paste the command corresponding to the "
            "game mode you want to play below:\n\n"
            f"**Solo:** `%wordchain play solo {ping}`\n"
            f"**Public:** `%wordchain play public {ping}`\n"
            f"**Lightning:** `%wordchain play lightning {ping}`\n"
            f"**Scrabble:** `%wordchain play scrabble {ping}`\n\n"
            "Have fun!"
        ))

    @w.command()
    async def leaderboard(self, ctx : discord.ApplicationContext):
        """View the Word Chain leaderboards."""
        psql1 = """
                SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, 
                    player_name, score
                FROM solo_wins
                LIMIT 10;
                """
        psql2 = """
                WITH solo_ranks AS (
                    SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, 
                        player, player_name, score
                    FROM solo_wins
                )
                SELECT rank, player_name, score
                FROM solo_ranks
                WHERE player = $1
                LIMIT 1;
                """
        psql7 = """
                SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, 
                    player_name, score
                FROM scrabble_wins
                LIMIT 10;
                """
        psql8 = """
                WITH scrabble_ranks AS (
                    SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, 
                        player, player_name, score
                    FROM scrabble_wins
                )
                SELECT rank, player_name, score
                FROM scrabble_ranks
                WHERE player = $1
                LIMIT 1;
                """
        async with self.bot.dictionary.acquire() as conn:
            # Top Solo Scores
            solo_board = await conn.fetch(psql1)
            solo_best = await conn.fetchrow(psql2, ctx.author.id)

            # I have decided not to do public/lightning leaderboards

            # Top Scrabble Scores
            scrabble_board = await conn.fetch(psql7)
            scrabble_best = await conn.fetchrow(psql8, ctx.author.id)

        # Write Solo Leaderboard
        solo_text = self.format_leaderboard(
            solo_board, ctx.author.name, solo_best['rank'], 
            solo_best['score'])
        solo_lb = discord.Embed(
            title="Word Chain Leaderboards: Solo High-Scores",
            description=solo_text,
            color=Vars.ABLUE)
        solo_lb.set_thumbnail(url=self.bot.user.avatar.url)

        # Write Scrabble Leaderboard
        scrabble_text = self.format_leaderboard(
            scrabble_board, ctx.author.name, scrabble_best['rank'],
            scrabble_best['score'])
        scrabble_lb = discord.Embed(
            title="Word Chain Leaderboards: Scrabble High-Scores",
            description=scrabble_text,
            color=Vars.ABLUE)
        scrabble_lb.set_thumbnail(url=self.bot.user.avatar.url)

        # Display embeds
        embeds = {
            "Solo" : solo_lb,
            "Scrabble" : scrabble_lb
        }
        view = discord.ui.View(timeout=30.0)
        view.add_item(LeaderboardMenu(ctx.author, embeds))
        await ctx.respond(embed=solo_lb, view=view)

    @w.command(name="check")
    async def _check(self, ctx, word : str):
        """See if a word exists in the Ayesha dictionary"""
        word = word.lower()
        psql = "SELECT id FROM word_list WHERE word = $1;"

        async with self.bot.dictionary.acquire() as conn:
            word_id = await conn.fetchval(psql, word)

        if word_id is None:
            return await ctx.respond(f"**{word}** is not in our database.")
        else:
            points = sum([point_conversion[c] for c in word])
            return await ctx.respond((
                f"**{word}** is a valid term for use in Word Chain!\n"
                f"Using it in Scrabble Mode nets **{points}** points."))


def setup(bot):
    bot.add_cog(Minigames(bot))