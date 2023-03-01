import discord

import asyncpg
import coolname

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
            self.attack = record['attack']
            self.crit = record['crit']
        else:
            self.is_empty = True
            self.weapon_id = None
            self.owner_id = None
            self.name = "No Weapon"
            self.type = "No Type"
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

        psql = "UPDATE items SET attack = $1 WHERE item_id = $2;"
        await conn.execute(psql, attack, self.weapon_id)

    async def destroy(self, conn : asyncpg.Connection):
        """Deletes this item from the database."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        psql = "DELETE FROM items WHERE item_id = $1"
        await conn.execute(psql, self.weapon_id)
        # self = Weapon() # remove this its getting in my way


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
    is_empty : bool
        Whether this object is a dummy object or not
    id : int
        The unique ID of the armor piece
    type : str
        The material this armor is made of (determing damage reduction)
    slot : str
        Whether this armor is a helmet, bodypiece, or boots
    owner_id : int
        The Discord ID of this piece's owner
    name : str
        A string combining type and slot for printing
    defense : int
        The damage reduction percentage of this armor piece
    """
    def __init__(self, record : asyncpg.Record = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the armor table.
            Pass nothing to create an empty armor piece.
        """
        if record is not None:
            self.is_empty = False
            self.id = record['armor_id']
            self.type = record['armor_type']
            self.slot = record['armor_slot']
            self.owner_id = record['user_id']
            self.name = f"{self.type} {self.slot}"
            self.defense = Vars.ARMOR_DEFENSE[self.slot][self.type]
        else:
            self.is_empty = True
            self.id = None
            self.type = "No Type"
            self.slot = "No Slot"
            self.owner_id = None
            self.name = "No Armor"
            self.defense = 0

    async def set_owner(self, conn : asyncpg.Connection, user_id : int):
        """Changes the owner of this armor."""
        if self.is_empty:
            raise Checks.EmptyObject

        self.owner_id = user_id

        psql = "UPDATE armor SET user_id = $1 WHERE armor_id = $2;"
        await conn.execute(psql, user_id, self.id)

    async def destroy(self, conn : asyncpg.Connection):
        """Deletes this item from the database."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        psql = "DELETE FROM armor WHERE armor_id = $1"
        await conn.execute(psql, self.id)


class Accessory:
    """An accessory object. Changing the object attributes are not permanent; to
    change a weapon's info, use the set-methods, which commit any changes
    to the object into the database. Unlike other game entities, accessories
    are relatively unchanged by gameplay.

    It is convenient for the bot to assume that a player always has an accessory
    equipped, so this class can also create empty objects by not passing
    a record upon instantiation. If a command alters the object's database
    values, it should first check the is_empty attribute to ensure such a change
    is possible. Changing an empty object will result in an EmptyObject error.

    Attributes
    ----------
    is_empty : bool
        Whether this object is a dummy object or not
    id : int
        This accessory's unique ID
    type : str 
        The material this accessory is made of (determing bonus magnitude)
    name : str
        A name for printing
    owner_id : int
        The Discord ID of the player who owns this accessory
    prefix : str
        The accessory's prefix, determining bonus
    """
    def __init__(self, record : asyncpg.Record = None):
        if record is not None:
            self.is_empty = False
            self.id = record['accessory_id']
            self.type = record['accessory_type']
            self.name = (f"{record['prefix']} {self.type} "
                         f"{record['accessory_name']}")
            self.owner_id = record['user_id']
            self.prefix = record['prefix']
            self.bonus = self._get_bonus()
        else:
            self.is_empty = True
            self.id = None
            self.type = "No Type"
            self.name = "No Accessory"
            self.owner_id = None
            self.prefix = "None"
            self.bonus = "No bonus"

    def _get_bonus(self):
        """Returns str outlining the bonus this accessory gives."""
        bonus = {
            "Lucky" : (
                f"This accessory gives a "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%` bonus to "
                f"gold and xp rewards from PvE, Travel, and Expeditions."),
            "Thorned" : (
                f"This accessory reflects "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%` of the "
                f"damage taken in PvE and PvP back to your enemy."
            ),
            "Strong" : (
                f"This accessory gives "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%` defense."
            ),
            "Shiny" : (
                f"The additional damage you take when an enemy lands a "
                f"critical strike on you is reduced by "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%`."
            ),
            "Flexible" : (
                f"Increase your crit rate by "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%`."
            ),
            "Thick" : (
                f"Increases your HP by "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%`."
            ),
            "Old" : (
                f"When you defeat a boss at level 25 or higher in PvE, gain "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}` gravitas."
            ),
            "Regal" : (
                f"You pay "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}%` less "
                f"in taxes."
            ),
            "Demonic" : (
                f"Increases your attack by "
                f"`{Vars.ACCESSORY_BONUS[self.prefix][self.type]}`."
            )
        }
        return bonus[self.prefix]

    async def destroy(self, conn : asyncpg.Connection):
        """Deletes this item from the database."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        psql = "DELETE FROM accessories WHERE accessory_id = $1"
        await conn.execute(psql, self.id)


async def get_weapon_by_id(conn : asyncpg.Connection, item_id : int) -> Weapon:
    """Return a weapon object of the item with the given ID."""
    psql = """
            SELECT
                item_id,
                weapontype,
                user_id,
                attack,
                crit,
                weapon_name
            FROM items
            WHERE item_id = $1;
            """
    
    weapon_record = await conn.fetchrow(psql, item_id)

    return Weapon(weapon_record)

async def create_weapon(conn : asyncpg.Connection, user_id : int,
        attack : int = None, crit : int = None, weapon_name : str = None, 
        weapon_type : str = None) -> Weapon:
    """Create a weapon with the specified information and returns it.
    Fields left blank will generate randomly
    """
    if attack is None:
        attack = random.choices(
            population=range(10,151), 
            weights=[30]*21 + [35]*20 + [40]*20 + [35]*20 + [30]*20 + \
                [20]*20 + [15]*8 + [10]*8 + [5]*4
        )[0]

    if crit is None:
        crit = random.choices(
            population=range(0,21), 
            weights=[7]*11 + [6, 5, 4, 3, 2, 2, 2, 1, 1, 1]
        )[0]

    if weapon_type is None:
        weapon_type = random.choice(Vars.WEAPON_TYPES)

    if weapon_name is None:
        weapon_name = _get_random_name()

    if weapon_type not in Vars.WEAPON_TYPES:
        raise Checks.InvalidWeaponType

    psql = """
            WITH rows AS (
                INSERT INTO items 
                    (weapontype, user_id, attack, crit, weapon_name)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING item_id
            )
            SELECT item_id FROM rows;
            """
    
    item_id = await conn.fetchval(psql, weapon_type, user_id, attack, crit, 
        weapon_name)

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

async def get_accessory_by_id(conn : asyncpg.Connection, 
        accessory_id : int) -> Accessory:
    """Return the accessory object of the piece with the given ID"""
    psql = """
            SELECT accessory_id, accessory_type, accessory_name, user_id, prefix
            FROM accessories
            WHERE accessory_id = $1;
            """
    accessory_record = await conn.fetchrow(psql, accessory_id)
    return Accessory(accessory_record)

async def create_accessory(conn : asyncpg.Connection, user_id : int, 
        type : str, prefix : str) -> Accessory:
    """Creates an accessory with the specified information and returns it."""
    if prefix not in Vars.ACCESSORY_BONUS.keys():
        raise Checks.InvalidAccessoryPrefix

    if type not in Vars.ACCESSORY_BONUS[prefix].keys():
        raise Checks.InvalidAccessoryMaterial

    name = random.choice(
        ["Necklace", "Pendant", "Earring", "Belt", "Ring", "Bracelet", 
         "Anklet", "Locket", "Lavaliere", "Pin", "Ribbon", "Dentures"])

    psql = """
            WITH rows AS (
                INSERT INTO accessories 
                    (accessory_type, accessory_name, user_id, prefix)
                VALUES ($1, $2, $3, $4)
                RETURNING accessory_id
            )
            SELECT accessory_id FROM rows;
            """
    accessory_id = await conn.fetchval(psql, type, name, user_id, prefix)
    return await get_accessory_by_id(conn, accessory_id)

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