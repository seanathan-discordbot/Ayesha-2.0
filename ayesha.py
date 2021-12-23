import nextcord
from nextcord.ext import commands

import logging
import traceback

import asyncpg

from Utilities import config

async def get_prefix(client, message):
    """Return the prefix of a server. If DM, return '%'."""
    a = isinstance(message.channel, nextcord.DMChannel)
    b = isinstance(message.channel, nextcord.GroupChannel)
    if a or b:
        return '%'

    conn = await asyncpg.connect(database = config.DATABASE['name'],
                                 user = config.DATABASE['user'],
                                 password = config.DATABASE['password'])
    psql = "SELECT prefix FROM prefixes WHERE server = $1"
    prefix = await conn.fetchval(psql, message.guild.id)

    if prefix is None:
        psql = "INSERT INTO prefixes (server, prefix) VALUES ($1, '%')"
        await conn.execute(psql, message.guild.id)
        prefix = '%'

    await conn.close()
    return prefix

class Ayesha(commands.AutoShardedBot):
    """Ayesha bot class with added properties"""

    def __init__(self):
        self.recent_voters = []

        super().__init__(
            command_prefix = get_prefix,
            case_insensitive = True
        )

        # Load Cogs
        self.init_cogs = (

        )

        for cog in self.init_cogs:
            try:
                self.load_extension(cog)
                print(f"Loaded cog {cog}.")
            except:
                print(f"Failed to load cog {cog}.")
                traceback.print_exc()

    @property
    def ayesha_blue(self):
        return 0xBEDCF6

    def is_admin(user_id : int):
        return user_id in config.ADMINS   

    async def on_ready(self):
        gp = "Read the %tutorial to get started!"
        self.loop.create_task(self.change_presence(activity=nextcord.Game(gp)))

        print("Ayesha is online.")

bot = Ayesha()

# Cog-loading commands
@bot.command()
@commands.check(bot.is_admin)
async def reload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")
    bot.load_extension(f"cogs.{extension}")
    await ctx.reply("Reloaded.")

# Add bot cooldown
_cd = commands.CooldownMapping.from_cooldown(1, 2.5, commands.BucketType.user)

@bot.check
async def cooldown_check(ctx):
    bucket = _cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after)
    return True

# Connect to database
async def create_db_pool():
    bot.db = await asyncpg.create_pool(database = config.DATABASE['name'],
                                       user = config.DATABASE['user'],
                                       password = config.DATABASE['password'])

bot.loop.run_until_complete(create_db_pool())

# Guild join and remove event handling
@bot.event
async def on_guild_join(guild):
    async with bot.db.acquire() as conn:
        psql = """
                INSERT INTO prefixes (server, prefix)
                VALUES ($1, '%')
                ON CONFLICT (server)
                DO UPDATE SET prefix = '%'
                """
        await conn.execute(psql, guild.id)

@bot.event
async def on_guild_remove(guild):
    async with bot.pg_con.acquire() as conn:
        await conn.execute("DELETE FROM prefixes WHERE server = $1", guild.id)

# Ping command
@bot.command()
async def ping(ctx):
    """Ping to see if bot is working."""
    fmt = f"Latency is {bot.latency * 1000:.2f} ms"
    embed = nextcord.Embed(title="Pong!", 
                           description=fmt, 
                           color=bot.ayesha_blue)
    await ctx.send(embed=embed)

bot.run(config.TOKEN)