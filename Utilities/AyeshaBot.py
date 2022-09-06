import discord
from discord.ext import commands

import traceback

import asyncpg

from Utilities import config, Vars

class Ayesha(commands.AutoShardedBot):
    """Ayesha bot class with added properties"""

    def __init__(self, cogs : list):
        self.init_cogs = cogs

        self.daily_claimers = {}
        self.recent_voters = {}
        self.trading_players = {}
        self.training_players = {}

        super().__init__(command_prefix = "%", case_insensitive = True)

        # Create connection pools of the bot databases
        self.db = self.loop.run_until_complete(create_db_pool())
        self.dictionary = self.loop.run_until_complete(create_dictionary_pool())

        # Load the bot cogs
        for cog in self.init_cogs:
            try:
                self.load_extension(cog)
                print(f"Loaded cog {cog}.")
            except:
                print(f"Failed to load cog {cog}.")
                traceback.print_exc()

    async def on_ready(self):
        gp = "Slash commands added!"
        self.loop.create_task(self.change_presence(activity=discord.Game(gp)))

        # Get Discord objects for later use
        self.announcement_channel = await self.fetch_channel(
            Vars.ANNOUNCEMENT_CHANNEL)
        self.raider_role = self.announcement_channel.guild.get_role(
            Vars.RAIDER_ROLE)

        print("Ayesha is online.")

    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.user.id in self.trading_players:
            return await interaction.response.send_message(
                f"Finish your trade first.")

        if interaction.user.id in self.training_players:
            if self.training_players[interaction.user.id] != interaction.custom_id:
                # NOTE: This entire operation exists solely to prevent this
                #   message from being printed after the training goes through
                #   i.e. this still printed when the player responded to the 
                #   original command. The things I have to do...
                return await interaction.response.send_message(
                    f"Finish your operation first.")

        return await super().on_interaction(interaction)

    def is_admin(self, ctx):
        return ctx.author.id in config.ADMINS


# Connect to database
async def create_db_pool():
    return await asyncpg.create_pool(
        database = config.DATABASE['name'],
        user = config.DATABASE['user'],
        password = config.DATABASE['password'])

# Word Chain database
async def create_dictionary_pool():
    return await asyncpg.create_pool(
        database = config.DICTIONARY['name'],
        user = config.DICTIONARY['user'],
        password = config.DICTIONARY['password'])