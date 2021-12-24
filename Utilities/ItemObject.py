import discord

import asyncpg
import coolname

import json
import random

from Utilities import Checks, Vars


class Weapon:
    """A weapon object. Changing the object attributes are not permanent; to
    change a weapon's stats, use the set-methods, which commit any changes
    to the object into the database.

    Attributes
    ----------
    weapon_id : int
        The weapon's unique ID
    owner_id : int
        The Discord ID of the weapon's owner
    name : str
        The name of the weapon
    type : str
        The object's weapon type
    rarity : str
        The rarity of the weapon
    attack : int
        The attack stat of the weapon
    crit : int
        The crit probability of the weapon

    Methods
    -------
    await set_owner()
        Change the owner of the weapon to the given ID.
    await set_name()
        Change the name of the weapon to the given string.
    await set_attack()
        Change the attack of the weapon to the given attack.
    await destroy()
        Deletes this item from the database.
    """
    def __init__(self, record : asyncpg.Connection = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the items table
            Pass nothing to create an empty weapon
        """
        if record is not None:
            self.weapon_id = record['item_id']
            self.owner_id = record['user_id']
            self.name = record['weapon_name']
            self.type = record['type']
            self.rarity = record['rarity']
            self.attack = record['attack']
            self.crit = record['crit']
        else:
            self.weapon_id = None
            self.owner_id = None
            self.name = "No Weapon"
            self.type = "No Type"
            self.rarity = "Common"
            self.attack = 0
            self.crit = 0

    async def set_owner(self, conn : asyncpg.Connection, user_id : int):
        """Changes the owner of this weapon."""
        self.owner_id = user_id

        psql = "UPDATE items SET user_id = $1 WHERE item_id = $2;"
        await conn.execute(psql, user_id, self.weapon_id)

    async def set_name(self, conn : asyncpg.Connection, name : str):
        """Changes the name of the weapon. 'name' must be <= 20 characters."""
        if len(name) > 20:
            raise Checks.ExcessiveCharacterCount(20)

        self.name = name

        psql = "UPDATE items SET weapon_name = $1 WHERE item_id = $2;"
        await conn.execute(psql, name, self.weapon_id)

    async def set_attack(self, conn : asyncpg.Connection, attack : int):
        """Changes the attack of the weapon."""
        self.attack = attack

        psql = "UPDATE items SET attack = $1 WHERE item_id $2;"
        await conn.execute(psql, attack, self.weapon_id)

    async def destroy(self, conn : asyncpg.Connection):
        """Deletes this item from the database."""
        psql = "DELETE FROM items WHERE item_id = $1"
        await conn.execute(psql, self.weapon_id)
        self = None


async def get_weapon_by_id(conn : asyncpg.Connection, item_id : int):
    """Return a weapon object of the item with the given ID."""
    psql = """
            SELECT
                item_id,
                weapontype,
                user_id,
                attack,
                crit,
                weapon_name,
                rarity
            FROM items
            WHERE item_id = $1;
            """
    
    weapon_record = await conn.fetchrow(psql, item_id)

    return Weapon(weapon_record)

async def create_weapon(conn : asyncpg.Connection, user_id : int, rarity : str,
        attack : int = None, crit : int = None, weapon_name : str = None, 
        weapon_type : str = None):
    """Create a weapon with the specified information and returns it.
    Fields left blank will generate randomly
    """
    if attack is None:
        attack = random.randint(Vars.RARITIES[rarity]['low_atk'], 
                                Vars.RARITIES[rarity]['high_atk'])

    if crit is None:
        crit = random.randint(Vars.RARITIES[rarity]['low_crit'], 
                              Vars.RARITIES[rarity]['high_crit'])

    if weapon_type is None:
        weapon_type = random.choice(Vars.WEAPON_TYPES)

    if weapon_name is None:
        weapon_name = _get_random_name()

    psql = """"
            WITH rows AS (
                INSERT INTO items 
                    (weapontype, user_id, attack, crit, weapon_name, rarity)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING item_id
            )
            SELECT item_id FROM rows;
            """
    
    item_id = conn.fetchval(psql, weapon_type, user_id, attack, 
                            crit, weapon_name, rarity)

    return get_weapon_by_id(conn, item_id)

def _get_random_name():
    """Returns a str: random combination of words up to 20 characters."""
    
    length = random.randint(1,3)

    if length == 1:
        name = coolname.generate()
        name = name[2]
    else:
        name = coolname.generate_slug(length)

    if len(name) > 20:
        name = name[0:20] 

    name = name.replace('-', ' ')
    name = name.title()

    return name