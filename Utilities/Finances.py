import asyncpg

from typing import List

from Utilities import Checks, PlayerObject, Vars

class Transaction:
    """A transaction class to streamline purchasing/selling things that
    involve taxation. This incorporates older methods which created dicts
    containing all information related to a transaction, but required
    remembering to use such methods in the correct way/order in each individual
    command.
    Transactions between players (eg offer) don't get taxed, so don't use this.

    Attributes
    ----------
    player : PlayerObject.Player
        The player to whom this transaction applies
    subtotal : int
        The amount (gold) the player would pay/be paid if there was no tax.
    tax_rate : float
        The tax rate being applied to the transaction
    tax_amount : int
        The amount being paid in taxes
    paying_price : int
        If the player is making a purchase, this is the total price they pay
    paid_amount : int
        If the player is making a sale, this is the total gold they make
    bonus_list : List[tuple]
        A list of things which have changed the transaction total
        The tuples take the form (bonus_amount (int), bonus_source (str))
    """
    def __init__(self, player : PlayerObject.Player, subtotal : int, 
            tax_rate : float, tax_amount : int, bonus_list : List[tuple] = []):
        """
        Parameters
        ----------
        player : PlayerObject.Player
            The player to whom this transaction applies
        subtotal : int
            The amount (gold) the player would pay/be paid if there was no tax.
        tax_rate : float
            The tax rate being applied to the transaction
        tax_amount : int
            The amount being paid in taxes
        bonus_list : Optional[List[tuple]]
            A list of things which have changed the transaction total
            The tuples take the form (bonus_amount (int), bonus_source (str))
        """
        self.player = player
        self.subtotal = subtotal
        self.tax_rate = tax_rate
        self.tax_amount = tax_amount
        self.paying_price = subtotal + tax_amount
        self.paid_amount = subtotal - tax_amount
        self.bonus_list = bonus_list

    @classmethod
    async def calc_cost(cls, conn : asyncpg.Connection, 
            player : PlayerObject.Player, subtotal : int, 
            sale_bonuses : List[tuple] = []):
        """Factory method for Transaction. Calculates everything.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to the database
        player : PlayerObject.Player
            The player to whom this transaction applies
        subtotal : int
            The amount (gold) the player would pay/be paid if there was no tax.
        sale_bonuses : Optional[List[tuple]]
            A list of things which have changed the transaction total
            The tuples take the form (bonus_amount (int), bonus_source (str))
        """
        multiplier = 1
        if player.origin == "Sunset":
            multiplier -= .05
        if player.occupation == "Scribe":
            multiplier -= .15
        if player.gravitas >= 200:
            multiplier -= .05
        elif player.gravitas >= 500:
            multiplier -= .15
        elif player.gravitas >= 1000:
            multiplier -= .25
        if player.accessory.prefix == "Regal":
            a_mult = Vars.ACCESSORY_BONUS["Regal"][player.accessory.type]
            multiplier -= a_mult / 100.0
        tax_rate = float(await get_tax_rate(conn)) * multiplier
        tax_amount = int(subtotal * tax_rate / 100)

        return cls(player, subtotal, tax_rate, tax_amount, sale_bonuses)

    @classmethod
    async def create_sale(cls, conn : asyncpg.Connection, 
            player : PlayerObject.Player, subtotal : int):
        """Method used when player is making a sale, applying sale bonuses
        based off their profile to the subtotal.

        Parameters
        ----------
        conn : asyncpg.Connection
            The connection to the database
        player : PlayerObject.Player
            The player to whom this transaction applies
        subtotal : int
            The amount (gold) the player would pay/be paid if there was no tax.
        """
        sale_bonus = 1
        sale_bonuses = []
        if player.occupation == "Merchant":
            sale_bonus += .5
            sale_bonuses.append((subtotal // 2), "Merchant")
        if player.assc.type == "Guild":
            guild_bonus = .5 + (.1 * player.assc.get_level())
            sale_bonus += guild_bonus
            sale_bonuses.append((int(subtotal * guild_bonus), "Guild Level"))
        subtotal = int(subtotal * sale_bonus)
        return await cls.calc_cost(conn, player, subtotal, sale_bonuses)

    async def log_transaction(self, conn : asyncpg.Connection, 
            type : str) -> str:
        """Pays or charges the player for the transaction based on the type
        passed. Also adds the log of this transaction to the database.
        Returns a string to display the player notifying them of their tax.

        type is either "purchase" or "sale".
        
        The return string is of the format: "You paid {tax} in taxes."
        """
        if type == "purchase":
            await self.player.give_gold(conn, self.paying_price*-1)
        elif type == "sale":
            await self.player.give_gold(conn, self.paid_amount)
        else:
            raise Checks.InvalidTransactionType

        psql = """
                INSERT INTO tax_transactions
                    (user_id, before_tax, tax_amount, tax_rate)
                VALUES ($1, $2, $3, $4);
                """
        await conn.execute(psql, self.player.disc_id, self.subtotal, 
            self.tax_amount, self.tax_rate)

        return f"You paid `{self.tax_amount}` in taxes."


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

# async def calc_cost_with_tax_rate(conn : asyncpg.Connection, 
#         subtotal : int, player_origin : str) -> dict:
#     """Returns a dict containing information about a transaction.
#     Dict Keys: subtotal, total, tax_rate, tax_amount
#     """
#     tax_rate = await get_tax_rate(conn)
#     if player_origin == 'Sunset':
#         tax_amount=int((subtotal*tax_rate/100)*0.95)
#     else:
#         tax_amount=int(subtotal*tax_rate/100)
#     return {
#         'subtotal' : subtotal,
#         'total' : subtotal + tax_amount,
#         'payout' : subtotal - tax_amount,
#         'tax_rate' : tax_rate,
#         'tax_amount' : tax_amount
#     }

# async def log_transaction(conn : asyncpg.Connection, user_id : int, 
#         subtotal : int, tax_amount : int, tax_rate : float):
#     """Log a transaction that has been fulfilled."""
#     psql = """
#             INSERT INTO tax_transactions
#                 (user_id, before_tax, tax_amount, tax_rate)
#             VALUES ($1, $2, $3, $4);
#             """
#     await conn.execute(psql, user_id, subtotal, tax_amount, tax_rate)

# def apply_sale_bonuses(gold : int, player : PlayerObject.Player) -> int:
#     """Adjusts the gold a player would receive in a sale based off any bonuses
#     such as guild, occupation, etc.
#     """
#     sale_bonus = 1
#     if player.occupation == "Merchant":
#         sale_bonus += .5
#     if player.assc.type == "Guild":
#         sale_bonus += .5 + (.1 * player.assc.get_level())
#     # TODO: Implement comptroller bonuses
#     return int(gold * sale_bonus)