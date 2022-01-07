import discord
from discord.ext import commands

import logging
import traceback

import asyncpg

from Utilities import config, Vars

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=config.LOG_FILE, 
                              encoding='utf-8', 
                              mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# async def get_prefix(client, message):
#     """Return the prefix of a server. If DM, return '%'."""
#     a = isinstance(message.channel, discord.DMChannel)
#     b = isinstance(message.channel, discord.GroupChannel)
#     if a or b:
#         return '%'

#     conn = await asyncpg.connect(database = config.DATABASE['name'],
#                                  user = config.DATABASE['user'],
#                                  password = config.DATABASE['password'])
#     psql = "SELECT prefix FROM prefixes WHERE server = $1"
#     prefix = await conn.fetchval(psql, message.guild.id)

#     if prefix is None:
#         psql = "INSERT INTO prefixes (server, prefix) VALUES ($1, '%')"
#         await conn.execute(psql, message.guild.id)
#         prefix = '%'

#     await conn.close()
#     return prefix

class Ayesha(commands.AutoShardedBot):
    """Ayesha bot class with added properties"""

    def __init__(self):
        self.recent_voters = {}
        self.trading_players = {}

        super().__init__(
            command_prefix = "$",
            case_insensitive = True
        )

        # Load Cogs
        self.init_cogs = (
            "cogs.Profile",
            "cogs.Error_Handler",
            "cogs.Items",
            "cogs.Travel",
            "cogs.Gacha",
            "cogs.Occupations",
            "cogs.Associations"
        )

        for cog in self.init_cogs:
            try:
                self.load_extension(cog)
                print(f"Loaded cog {cog}.")
            except:
                print(f"Failed to load cog {cog}.")
                traceback.print_exc()

    def is_admin(self, ctx):
        return ctx.author.id in config.ADMINS   

    async def on_ready(self):
        gp = "Slash commands added!"
        self.loop.create_task(self.change_presence(activity=discord.Game(gp)))

        print("Ayesha is online.")

    async def on_interaction(self, interaction):
        if interaction.user.id in self.trading_players:
            return await interaction.response.send_message(
                f"Finish your trade first.")

        return await super().on_interaction(interaction)

bot = Ayesha()

# Cog-loading commands
# @bot.slash_command(guild_ids=[762118688567984151])
# @commands.check(bot.is_admin)
# async def reload(ctx, extension):
#     bot.unload_extension(f"cogs.{extension}")
#     bot.load_extension(f"cogs.{extension}")
#     await ctx.respond("Reloaded.")

# @bot.slash_command(guild_ids=[762118688567984151])
# @commands.check(bot.is_admin)
# async def load(ctx, extension):
#     bot.load_extension(f"cogs.{extension}")
#     await ctx.respond("Loaded.")

# @bot.slash_command(guild_ids=[762118688567984151])
# @commands.check(bot.is_admin)
# async def unload(ctx, extension):
#     bot.unload_extension(f"cogs.{extension}")
#     await ctx.respond("Unloaded.")

# Connect to database
async def create_db_pool():
    bot.db = await asyncpg.create_pool(database = config.DATABASE['name'],
                                       user = config.DATABASE['user'],
                                       password = config.DATABASE['password'])

bot.loop.run_until_complete(create_db_pool())

# Guild join and remove event handling
# @bot.event
# async def on_guild_join(guild):
#     async with bot.db.acquire() as conn:
#         psql = """
#                 INSERT INTO prefixes (server, prefix)
#                 VALUES ($1, '%')
#                 ON CONFLICT (server)
#                 DO UPDATE SET prefix = '%'
#                 """
#         await conn.execute(psql, guild.id)

# @bot.event
# async def on_guild_remove(guild):
#     async with bot.pg_con.acquire() as conn:
#         await conn.execute("DELETE FROM prefixes WHERE server = $1", guild.id)

# Ping command
@bot.slash_command(guild_ids=[762118688567984151])
async def ping(ctx):
    """Ping to see if bot is working."""
    fmt = f"Latency is {bot.latency * 1000:.2f} ms"
    embed = discord.Embed(title="Pong!", 
                           description=fmt, 
                           color=Vars.ABLUE)
    await ctx.respond(embed=embed)

bot.run(config.TOKEN)