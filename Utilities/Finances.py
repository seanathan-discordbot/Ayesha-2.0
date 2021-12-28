
import asyncpg
async def get_tax_rate(pool):
    """Returns the current bot-wide tax rate."""
    async with pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT tax_rate FROM tax_rates ORDER BY id DESC LIMIT 1')

async def get_tax_info(pool):
    """Return info related to the curent tax rate."""
    async with pool.acquire() as conn:
        tax_info = await conn.fetchrow("""
                                    SELECT tax_rates.tax_rate, players.user_name
                                    , 
                                    tax_rates.setdate
                                    FROM tax_rates
                                    INNER JOIN players
                                        ON players.user_id = tax_rates.setby
                                    ORDER BY id DESC
                                    LIMIT 1""")
        collected = await conn.fetchval("""
                                    WITH start_date AS (
                                        SELECT setdate
                                        FROM officeholders
                                        WHERE office = 'Mayor'
                                        ORDER BY setdate DESC
                                        LIMIT 1
                                    )
                                    SELECT SUM(tax_amount)
                                    FROM tax_transactions
                                    WHERE time > (SELECT * FROM start_date);""")

        tax_output = dict(tax_info)
        tax_output['Total_Collection'] = collected

        return tax_output

async def set_tax_rate(pool,tax_rate: float, setby: int):
    """sets the tax rate """
    async with pool.acquire() as conn:
        await conn.execute(
                        'INSERT INTO tax_rates (tax_rate, setby) VALUES ($1, $2)'
                        , tax_rate, setby)
        await pool.release(conn)

async def calc_cost_with_tax_rate(pool,subtotal,player_origin):
    tax_rate=await get_tax_rate(pool)
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
async def log_transaction(pool,user_id : int,subtotal : int, tax_amount : int, 
        tax_rate : float):
    """Log a transaction that has been fulfilled."""
    async with pool.acquire() as conn:
        await conn.execute("""
                        INSERT INTO tax_transactions
                        (user_id, before_tax, tax_amount, tax_rate)
                        VALUES ($1, $2, $3, $4),
                        user_id, subtotal, tax_amount, tax_rate""")
        await pool.release(conn)