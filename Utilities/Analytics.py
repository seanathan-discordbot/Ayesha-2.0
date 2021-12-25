import asyncpg

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
    return await conn.fetchval(psql, user_id)

async def xp_leaderboard(conn : asyncpg.Connection, 
        user_id : int, amount : int = 10):
    """Orders all players by xp and returns a"""
    psql = """
            SELECT ROW_NUMBER() OVER (ORDER BY xp DESC) AS rank, 
                user_id, user_name, xp
            FROM players
            LIMIT 10;
            """

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
    return await conn.fetchval(psql, user_id)

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
    return await conn.fetchval(psql, user_id)

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
    return await conn.fetchval(psql, user_id)

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
    return await conn.fetchval(psql, user_id)