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

    It is convenient for the bot to assume that a player always has a weapon
    equipped, so this class can also create empty objects by not passing
    a record upon instantiation. If a command alters the object's database
    values, it should first check the is_empty attribute to ensure such a change
    is possible. Changing an empty object will result in an EmptyObject error.

    Attributes
    ----------
    is_empty : bool
        Whether this object is a dummy object or not
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
    """
    def __init__(self, record : asyncpg.Record = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the items table
            Pass nothing to create an empty weapon
        """
        if record is not None:
            self.is_empty = False
            self.weapon_id = record['item_id']
            self.owner_id = record['user_id']
            self.name = record['weapon_name']
            self.type = record['weapontype']
            self.rarity = record['rarity']
            self.attack = record['attack']
            self.crit = record['crit']
        else:
            self.is_empty = True
            self.weapon_id = None
            self.owner_id = None
            self.name = "No Weapon"
            self.type = "No Type"
            self.rarity = "Common"
            self.attack = 0
            self.crit = 0

    async def set_owner(self, conn : asyncpg.Connection, user_id : int):
        """Changes the owner of this weapon."""
        if self.is_empty:
            raise Checks.EmptyObject

        self.owner_id = user_id

        psql = "UPDATE items SET user_id = $1 WHERE item_id = $2;"
        await conn.execute(psql, user_id, self.weapon_id)

    async def set_name(self, conn : asyncpg.Connection, name : str):
        """Changes the name of the weapon. 'name' must be <= 20 characters."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        if len(name) > 20:
            raise Checks.ExcessiveCharacterCount(20)

        self.name = name

        psql = "UPDATE items SET weapon_name = $1 WHERE item_id = $2;"
        await conn.execute(psql, name, self.weapon_id)

    async def set_attack(self, conn : asyncpg.Connection, attack : int):
        """Changes the attack of the weapon."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        self.attack = attack

        psql = "UPDATE items SET attack = $1 WHERE item_id $2;"
        await conn.execute(psql, attack, self.weapon_id)

    async def destroy(self, conn : asyncpg.Connection):
        """Deletes this item from the database."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        psql = "DELETE FROM items WHERE item_id = $1"
        await conn.execute(psql, self.weapon_id)
        self = Weapon()

class Armor:
    """An armor object. Changing the object attributes are not permanent; to
    change a weapon's info, use the set-methods, which commit any changes
    to the object into the database. Unlike other game entities, armor
    is relatively unchanged by gameplay.

    It is convenient for the bot to assume that a player always has armor
    equipped, so this class can also create empty objects by not passing
    a record upon instantiation. If a command alters the object's database
    values, it should first check the is_empty attribute to ensure such a change
    is possible. Changing an empty object will result in an EmptyObject error.

    Attributes
    ----------
    """
    def __init__(self, record : asyncpg.Record = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the armor table
            Pass nothing to create an empty weapon
        """
        if record is not None:
            self.is_empty = False
            self.id = record['armor_id']
            self.type = record['armor_type']
            self.slot = record['armor_slot']
            self.owner_id = record['user_id']
            self.name = f"{self.type} {self.type}"
            self.defense = Vars.ARMOR_DEFENSE[self.slot][self.type]
        else:
            self.is_empty = True
            self.id = None
            self.type = "No Type"
            self.slot = "No Slot"
            self.owner_id = None
            self.name = "No Armor"
            self.defense = 0


async def get_weapon_by_id(conn : asyncpg.Connection, item_id : int) -> Weapon:
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
        weapon_type : str = None) -> Weapon:
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

    if weapon_type not in Vars.WEAPON_TYPES:
        raise Checks.InvalidWeaponType

    psql = """
            WITH rows AS (
                INSERT INTO items 
                    (weapontype, user_id, attack, crit, weapon_name, rarity)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING item_id
            )
            SELECT item_id FROM rows;
            """
    
    item_id = await conn.fetchval(psql, weapon_type, user_id, attack, crit, 
        weapon_name, rarity)

    return await get_weapon_by_id(conn, item_id)

async def get_armor_by_id(conn : asyncpg.Connection, armor_id : int) -> Armor:
    """Return the armor object of the piece with the given ID"""
    psql = """
            SELECT armor_id, armor_type, armor_slot, user_id
            FROM armor
            WHERE armor_id = $1;
            """
    armor_record = await conn.fetchrow(psql, armor_id)
    return Armor(armor_record)

async def create_armor(conn : asyncpg.Connection, user_id : int, type : str,
        material : str) -> Armor:
    """Creates an armorpiece with the specified information and returns it."""
    if type not in Vars.ARMOR_DEFENSE.keys():
        raise Checks.InvalidArmorType

    if material not in Vars.ARMOR_DEFENSE[type].keys():
        raise Checks.InvalidArmorMaterial

    psql = """
            WITH rows AS (
                INSERT INTO armor (armor_type, armor_slot, user_id)
                VALUES ($1, $2, $3)
                RETURNING armor_id
            )
            SELECT armor_id FROM rows;
            """
    armor_id = await conn.fetchval(psql, material, type, user_id)
    return await get_armor_by_id(conn, armor_id)

def _get_random_name() -> str:
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