import nextcord

import asyncpg
import coolname

import json
import random

from Utilities import config, Checks

RARITIES = {
    'Common' : {
        'low_atk' : 10,
        'high_atk' : 30,
        'low_crit' : 0,
        'high_crit' : 5
    },
    'Uncommon' : {
        'low_atk' : 30,
        'high_atk' : 60,
        'low_crit' : 0,
        'high_crit' : 5
    },
    'Rare' : {
        'low_atk' : 45,
        'high_atk' : 90,
        'low_crit' : 0,
        'high_crit' : 10
    },
    'Epic' : {
        'low_atk' : 75,
        'high_atk' : 120,
        'low_crit' : 0,
        'high_crit' : 15
    },
    'Legendary' : {
        'low_atk' : 100,
        'high_atk' : 150,
        'low_crit' : 5,
        'high_crit' : 20
    }
}

WEAPON_TYPES = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 
                'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 
                'Mace']

class Player:
    """The Ayesha character object

    Attributes
    ----------


    Methods
    -------
    
    """
    def __init__(self, record : asyncpg.Record):
        """
        Parameters
        ----------
        record : asyncpg.Record
            A record containing information from the players table
        """
        self.disc_id = record['user_id']
        self.unique_id = record['num']
        self.char_name = record['user_name']
        self.xp = record['xp']
        self.level = self.get_level(self.xp)
        self.equipped_item = get_weapon_by_id(record['equipped_item'])
        self.acolyte1 = get_acolyte_by_id(record['acolyte1'])
        self.acolyte2 = get_acolyte_by_id(record['acolyte2'])
        self.assc = record['assc']
        self.guild_rank = record['guild_rank']
        self.gold = record['gold']
        self.occupation = record['occupation']
        self.location = record['loc']
        self.pvp_wins = record['pvpwins']
        self.pvp_fights = record['pvpfights']
        self.boss_wins = record['bosswins']
        self.boss_fights = record['bossfights']
        self.rubidics = record['rubidics']
        self.pity_counter = record['pitycounter']
        self.adventure = record['adventure']
        self.destination = record['destination']
        self.gravitas = record['gravitas']
        self.daily_streak = record['daily_streak']

    def get_level(self):
        """Returns the player's level."""
        def f(x):
            return int(20 * x**3 + 500)
        
        def g(x):
            return int(2/5 * x**4 + 250000)

        if self.xp <= 540500: # Simpler scaling for first 30 levels
            level = 0
            while (self.xp >= f(level)):
                level += 1
        else:
            level = 31
            while (self.xp >= f(level)):
                level += 1

        return level - 1

    async def is_weapon_owner(self, conn : asyncpg.Connection, item_id : int):
        """Returns true/false depending on whether the item with the given 
        ID is in this player's inventory.
        """
        psql = """
                SELECT item_id FROM items
                WHERE user_id = $1 AND item_id = $2;
                """
        val = await conn.fetchval(conn, self.disc_id, item_id)

        return val is not None

    async def equip_item(self, conn : asyncpg.Connection, item_id : int):
        """Equips an item on the player."""
        if not self.is_weapon_owner(conn, item_id):
            raise Checks.NotWeaponOwner

        self.equipped_item = get_weapon_by_id(conn, item_id)

        psql = """
                UPDATE players 
                SET equipped_item = $1
                WHERE user_id = $2;
                """
        await conn.execute(psql, item_id, self.disc_id)

    async def unequip_item(self, conn: asyncpg.Connection):
        """Unequips the current item from the player."""
        self.equipped_item = None

        psql = """
                UPDATE players SET equipped_item = NULL WHERE user_id = $1;
                """
        await conn.execute(psql, self.disc_id)

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
    set_owner(asyncpg.Connection, int)
        Change the owner of the weapon to the given ID.
    set_name(asyncpg.Connection, str)
        Change the name of the weapon to the given string.
    set_attack(asyncpg.Connection, int)
        Change the attack of the weapon to the given attack.
    destroy()
        Deletes this item from the database.
    """
    def __init__(self, record : asyncpg.Connection=None):
        """
        Parameters
        ----------
        record : asyncpg.Record
            A record containing information from the items table
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

class Acolyte:
    """An acolyte object.

    Attributes
    ----------

    Methods
    -------
    
    """
    def __init__(self, record : asyncpg.Record=None):
        """
        Parameters
        ----------
        """
        if record is not None:
            self.gen_dict = self.get_acolyte_by_name(record['acolyte_name'])
            self.acolyte_id = record['acolyte_id']
            self.owner_id = record['user_id']
            self.acolyte_name = record['acolyte_name']
            self.xp = record['xp']
            self.level = self.get_level(record['xp'])
            self.dupes = 10 if record['duplicate'] > 10 else record['duplicate']
        else:
            self.gen_dict = {
                'Name' : None,
                'Attack' : 0,
                'Scale' : 0,
                'Crit' : 0,
                'HP' : 0,
                'Rarity' : 0,
                'Effect' : None,
                'Mat' : None,
                'Story' : None,
                'Image' : None
            }
            self.acolyte_id = None
            self.owner_id = None
            self.acolyte_name = None
            self.xp = 0
            self.level = 0
            self.dupes = 0

    def get_acolyte_by_name(name : str):
        """
        Returns a dict of the general information of the acolyte.
        Dict: Name, Attack, Scale, Crit, HP, Rarity, Effect, Mat, Story, Image
        """
        with open(config.ACOLYTE_LIST_PATH, 'r') as acolyte_list:
            return json.load(acolyte_list)[name]

    def get_level(xp : int):
        """Returns the acolyte's level."""
        def f(x):
            return int(300 * (x**2))

        level = 0
        while (xp >= f(level)):
            level += 1
        level -= 1

        if level > 100:
            level = 100

        return level

    def get_attack(self):
        """Returns the acolyte's attack stat."""
        # Max 10 duplicates go into stat calculation
        if self.dupes > 10:
            self.dupes = 10

        # Duplicates give bonuses depending on acolyte rarity
        if self.gen_dict['Rarity'] == 5:
            attack = self.duplicate * 3

        attack += self.gen_dict['Attack']
        attack += self.level * self.gen_dict['Scale']

        return attack

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
    weapon_type : str = None
):
    """Create a weapon with the specified information and returns it.
    Fields left blank will generate randomly
    """
    if attack is None:
        attack = random.randint(RARITIES[rarity]['low_atk'], 
                                RARITIES[rarity]['high_atk'])

    if crit is None:
        crit = random.randint(RARITIES[rarity]['low_crit'], 
                              RARITIES[rarity]['high_crit'])

    if weapon_type is None:
        weapon_type = random.choice(WEAPON_TYPES)

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

async def get_player_by_id(conn : asyncpg.Connection, user_id : int):
    """Return a player object of the player with the given Discord ID."""
    psql = """
            SELECT 
                num,
                user_id,
                user_name,
                xp,
                equipped_item,
                acolyte1,
                acolyte2,
                assc,
                guild_rank,
                gold,
                occupation,
                loc,
                pvpwins,
                pvpfights,
                bosswins,
                bossfights,
                rubidics,
                pitycounter,
                adventure,
                destination,
                gravitas,
                daily_streak
            FROM players
            WHERE user_id = $1;
            """
    
    player_record = await conn.fetchrow(psql, user_id)

    return Player(player_record)

async def create_character(conn : asyncpg.Connection, user_id : int, name : str):
    """Creates and returns a profile for the user with the given Discord ID."""
    psql = """
            INSERT INTO players (user_id, user_name) VALUES ($1, $2);
            INSERT INTO resources (user_id) VALUES ($1);
            INSERT INTO strategy (user_id) VALUES ($1);
            """
    await conn.execute(psql, user_id, name)

    item = await create_weapon(conn, user_id, "Common", attack=20, crit=0, 
                               weapon_name="Wooden Spear", weapon_type="Spear")

    return await get_player_by_id(conn, user_id)

async def get_acolyte_by_id(conn : asyncpg.Connection, acolyte_id : int):
    """Return an acolyte object of the acolyte with the given ID."""
    psql = """
            SELECT acolyte_id, user_id, acolyte_name, xp, duplicate
            FROM acolytes
            WHERE acolyte_id = $1
            """
    acolyte_record = await conn.fetchrow(psql, acolyte_id)

    return Acolyte(acolyte_id)