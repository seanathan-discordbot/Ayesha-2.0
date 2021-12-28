import asyncpg

async def get_tax_rate(conn : asyncpg.Connection) -> float:
    """Returns the current bot-wide tax rate."""
    psql = """
            SELECT tax_rate 
            FROM tax_rates 
            ORDER BY id DESC 
            LIMIT 1;
            """
    return await conn.fetchval(psql)

async def get_tax_info(conn : asyncpg.Connection) -> dict:
    """Return info related to the curent tax rate.
    Dict Keys: tax_rate, user_name (who set the rate), setdate, 
        collected (total collected over this period)
    """
    psql1 = """
            SELECT tax_rates.tax_rate, players.user_name, tax_rates.setdate
            FROM tax_rates
            INNER JOIN players
                ON players.user_id = tax_rates.setby
            ORDER BY id DESC
            LIMIT 1;
            """
    psql2 = """
            WITH start_date AS (
                SELECT setdate
                FROM officeholders
                WHERE office = 'Mayor'
                ORDER BY setdate DESC
                LIMIT 1
            )
            SELECT SUM(tax_amount)
            FROM tax_transactions
            WHERE time > (SELECT * FROM start_date);
            """

    tax_output = dict(await conn.fetchrow(psql1))
    tax_output['Collected'] = await conn.fetchval(psql2)

    return tax_output

async def set_tax_rate(conn : asyncpg.Connection, tax_rate: float, setby: int):
    """Sets the tax rate."""
    psql = """INSERT INTO tax_rates (tax_rate, setby) VALUES ($1, $2);"""
    await conn.execute(psql, tax_rate, setby)

async def calc_cost_with_tax_rate(conn : asyncpg.Connection, 
        subtotal : int, player_origin : str) -> dict:
    """Returns a dict containing information about a transaction.
    Dict Keys: subtotal, total, tax_rate, tax_amount
    """
    tax_rate = await get_tax_rate(conn)
    if player_origin == 'Sunset':
        tax_amount=int((subtotal*tax_rate/100)*0.95)
    else:
        tax_amount=int(subtotal*tax_rate/100)
    return {
        'subtotal' : subtotal,
        'total' : subtotal + tax_amount,
        'tax_rate' : tax_rate,
        'tax_amount' : tax_amount
    }

async def log_transaction(conn : asyncpg.Connection, user_id : int, 
        subtotal : int, tax_amount : int, tax_rate : float):
    """Log a transaction that has been fulfilled."""
    psql = """
            INSERT INTO tax_transactions
                (user_id, before_tax, tax_amount, tax_rate)
            VALUES ($1, $2, $3, $4);
            """
    await conn.execute(psql, user_id, subtotal, tax_amount, tax_rate)