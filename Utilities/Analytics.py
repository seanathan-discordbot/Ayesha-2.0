import asyncpg
from typing import List

async def get_xp_rank(conn : asyncpg.Connection, user_id : int) -> int:
    """Returns the rank in xp for the player given"""
    psql = """
            WITH ranks AS (
                SELECT ROW_NUMBER() OVER (ORDER BY xp DESC) AS rank, 
                    user_id, user_name, xp
                FROM players
            )
            SELECT rank, user_id, user_name, xp
            FROM ranks
            WHERE user_id = $1
            LIMIT 1;
            """
    return await conn.fetchval(psql, user_id, timeout=0.2)

async def get_gold_rank(conn : asyncpg.Connection, user_id : int) -> int:
    """Returns the rank in gold for the player given"""
    psql = """
            WITH ranks AS (
                SELECT ROW_NUMBER() OVER (ORDER BY gold DESC) AS rank, 
                    user_id, user_name, gold
                FROM players
            )
            SELECT rank, user_id, user_name, gold
            FROM ranks
            WHERE user_id = $1
            LIMIT 1;
            """
    return await conn.fetchval(psql, user_id, timeout=0.2)

async def get_gravitas_rank(conn : asyncpg.Connection, user_id : int) -> int:
    """Returns the rank in gravitas for the player given"""
    psql = """
            WITH ranks AS (
                SELECT ROW_NUMBER() OVER (ORDER BY gravitas DESC) AS rank, 
                    user_id, user_name, gravitas
                FROM players
            )
            SELECT rank, user_id, user_name, gravitas
            FROM ranks
            WHERE user_id = $1
            LIMIT 1;
            """
    return await conn.fetchval(psql, user_id, timeout=0.2)

async def get_bosswins_rank(conn : asyncpg.Connection, user_id : int) -> int:
    """Returns the rank in bosswins for the player given"""
    psql = """
            WITH ranks AS (
                SELECT ROW_NUMBER() OVER (ORDER BY bosswins DESC) AS rank, 
                    user_id, user_name, bosswins
                FROM players
            )
            SELECT rank, user_id, user_name, bosswins
            FROM ranks
            WHERE user_id = $1
            LIMIT 1;
            """
    return await conn.fetchval(psql, user_id, timeout=0.2)

async def get_boss_level_rank(conn : asyncpg.Connection, user_id : int) -> int:
    """Returns the rank in order of players.pve_limit"""
    psql = """
            WITH ranks AS (
                SELECT ROW_NUMBER() OVER (ORDER BY pve_limit DESC) AS rank, 
                    user_id, user_name, pve_limit
                FROM players
            )
            SELECT rank, user_id, user_name, pve_limit
            FROM ranks   
            WHERE user_id = $1
            LIMIT 1;
            """
    return await conn.fetchval(psql, user_id, timeout=0.2)

async def get_pvpwins_rank(conn : asyncpg.Connection, user_id : int) -> int:
    """Returns the rank in pvpwins for the player given"""
    psql = """
            WITH ranks AS (
                SELECT ROW_NUMBER() OVER (ORDER BY pvpwins DESC) AS rank, 
                    user_id, user_name, pvpwins
                FROM players
            )
            SELECT rank, user_id, user_name, pvpwins
            FROM ranks
            WHERE user_id = $1
            LIMIT 1;
            """
    return await conn.fetchval(psql, user_id, timeout=0.2)

def stringify_rank(rank : int) -> str:
    """Converts the rank into a str. eg Rank 1 --> 1st"""
    if rank is None:
        return ">100th"

    output = str(rank)

    if output[-2:] in ("11", "12", "13"):
        output += "th"
    elif output[-1] == '1':
        output += "st"
    elif output[-1] == '2':
        output += "nd"
    elif output[-1] == '3':
        output += "rd"
    else:
        output += "th"

    return output

async def get_econ_info(conn : asyncpg.Connection):
    """Returns a record containing some information about the bot economy.
    Keys: g (total gold), r (total rubidics)
    """
    psql = """
            SELECT 
                SUM(gold) as g,
                SUM(rubidics) AS r
            FROM players;
            """
    return await conn.fetchrow(psql)

async def get_acolyte_info(conn : asyncpg.Connection):
    """Returns a list of records containing most equipped acolytes.
    Length of the list is 3.
    Keys: acolyte_name, c (amount of people with said acolyte equipped)
    """
    psql = """
            SELECT acolytes.acolyte_name, COUNT(acolytes.acolyte_name) as c
            FROM acolytes
            RIGHT JOIN players
                ON acolytes.acolyte_id = players.acolyte1
                    OR acolytes.acolyte_id = players.acolyte2
            GROUP BY acolytes.acolyte_name
            ORDER BY c DESC
            LIMIT 3;
            """
    return await conn.fetch(psql)

async def get_combat_info(conn : asyncpg.Connection):
    """Returns idk
    Keys: b (total bosswins), p (total pvpfights)
    """
    psql = """
            SELECT SUM(bosswins) AS b, SUM(pvpfights)/2 AS p
            FROM players;
            """
    return await conn.fetchrow(psql)

async def get_top_xp(conn : asyncpg.Connection):
    """Returns a list of records containing the top 10 players by xp
    Record: user_name, xp 
    """
    psql = """
            SELECT user_name, xp
            FROM players
            ORDER BY xp DESC LIMIT 10;
            """
    return await conn.fetch(psql)

async def get_top_gold(conn : asyncpg.Connection):
    """Returns a list of records containing the top 10 players by gold
    Record: user_name, gold
    """
    psql = """
            SELECT user_name, gold
            FROM players
            ORDER BY gold DESC LIMIT 10;
            """
    return await conn.fetch(psql)

async def get_top_pve(conn : asyncpg.Connection):
    """Returns a list of records containing the top 10 players by PvE wins
    Record: user_name, bosswins
    """
    psql = """
            SELECT user_name, bosswins
            FROM players
            ORDER BY bosswins DESC LIMIT 10;
            """
    return await conn.fetch(psql)

async def get_top_pvp(conn : asyncpg.Connection):
    """Returns a list of records containing the top 10 players by PvP wins
    Record: user_name, pvpwins
    """
    psql = """
            SELECT user_name, pvpwins
            FROM players
            ORDER BY pvpwins DESC LIMIT 10;
            """
    return await conn.fetch(psql)

async def get_top_gravitas(conn : asyncpg.Connection):
    """Returns a list of records containing the top 10 players by gravitas
    Record: user_name, gravitas
    """
    psql = """
            SELECT user_name, gravitas
            FROM players
            ORDER BY gravitas DESC LIMIT 10;
            """
    return await conn.fetch(psql)

def stringify_gains(item : str, total : int, sources : List[tuple]):
    """
    Break down all bonuses to some item and returns a str detailing it.
    total is the base amount gained after all bonuses are applied.
    Each arg is a bonus source given as a tuple, with the bonus amount first,
    followed by the name of the source eg (20, 'Occupation')
    """
    output = f"`{total}` {item}"
    additions = [f"(`{source[0]}` from {source[1]})" for source in sources]
    if len(sources) > 0:
        output += " "
        output += " ".join(additions)
    return output