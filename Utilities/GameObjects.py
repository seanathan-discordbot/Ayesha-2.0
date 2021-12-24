import discord

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
    disc_id : int
        The player's Discord ID
    unique_id : int
        A unique ID for miscellaneous purposes. 
        Use disc_id for a proper identifier
    char_name : int
        The player character's name (set by player, not their Discord username)
    xp : int
        The player's xp points
    level : int
        The player's level
    equipped_item : GameObjects.Weapon
        The weapon object of the item equipped by the player
    acolyte1 : GameObjects.Acolyte
        The acolyte object of the acolyte equipped by the player in Slot 1
    acolyte2 : GameObjects.Acolyte
        The acolyte object of the acolyte equipped by the player in Slot 2
    assc : int (Changes to GameObject.Association when possible)
        The ID of the association this player is in
    guild_rank : str
        The rank the player holds in the association they are in
    gold : int
        The player's wealth in gold (general currency)
    occupation : str
        The player's class/occupation role
    location : str
        The location of the player on the map
    pvp_wins : int
        The amount of wins the player has in PvP battles
    pvp_fights : int
        The total amount of PvP battles the player has participated in
    boss_wins : int
        The amount of wins the player has in PvE battles
    boss_fights : int
        The total amount of PvE battles the player has participated in
    rubidics : int
        The player's wealth in rubidics (gacha currency)
    pity_counter : int
        The amount of gacha pulls the player has done since their last 
        legendary weapon or 5-star acolyte
    adventure : int
        The endtime (time.time()) of the player's adventure
    destination : str
        The destination of the player's adventure on the map
    gravitas : int
        The player's wealth in gravitas (alternate currency)
    daily_streak : int
        The amount of days in a row the player has used the `daily` command

    Methods
    -------
    get_level()
        Returns the player's level using its current xp value
    await is_weapon_owner()
        Returns a bool of whether the item with the ID passed is in the player's
        inventory
    await equip_item()
        Equips the item with the passed ID to the player
    await unequip_item()
        Replaces the equipped_item with an empty weapon and nullifies the
        equipped_item in the database
    await is_acolyte_owner()
        Returns a bool of whether the acolyte with the ID passed is in the 
        player's tavern
    await equip_acolyte()
        Equips the acolyte with the passed ID to the player in the given slot
    await unequip_acolyte()
        Replaces the acolyte with an empty one and nullifies the acolyte in the
        database in the slot passed    
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
        self.level = self.get_level()
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
            while (self.xp >= g(level)):
                level += 1

        return level - 1

    async def check_xp_increase(self, conn : asyncpg.Connection, 
            ctx : discord.context, xp : int):
        """Increase the player's xp by a set amount.
        This will also increase the player's equipped acolytes xp by 10% of the 
        player's increase.
        If the xp change results in a level-up for any of these entities, 
        a reward will be given and printed to Discord.        
        """
        old_level = self.level
        self.xp += xp
        psql = """
                UPDATE players
                SET xp = xp + $1
                WHERE user_id = $2;
                """
        await conn.execute(psql, xp, self.disc_id)
        self.level = self.get_level()
        if self.level > old_level: # Level up
            gold = self.level * 500
            rubidics = int(self.level / 30) + 1

            self.give_gold(conn, gold)
            self.give_rubidics(conn, rubidics)

            embed = discord.Embed(
                title = f"You have levelled up to level {self.level}!",
                color = config.ABLUE)
            embed.add_field(
                name = f"{self.char_name}, you gained some rewards",
                value = f"**Gold:** {gold}\n**Rubidics:**{rubidics}")

            await ctx.respond(embed=embed)

        # Check xp for the equipped acolytes
        a_xp = int(xp / 10)
        if self.acolyte1.acolyte_name is not None:
            await self.acolyte1.check_xp_increase(conn, ctx, a_xp)

        if self.acolyte2.acolyte_name is not None:
            await self.acolyte2.check_xp_increase(conn, ctx, a_xp)

    async def is_weapon_owner(self, conn : asyncpg.Connection, item_id : int):
        """Returns true/false depending on whether the item with the given 
        ID is in this player's inventory.
        """
        psql = """
                SELECT item_id FROM items
                WHERE user_id = $1 AND item_id = $2;
                """
        val = await conn.fetchval(self.disc_id, item_id)

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
        self.equipped_item = Weapon() # Create an empty weapon

        psql = """
                UPDATE players SET equipped_item = NULL WHERE user_id = $1;
                """
        await conn.execute(psql, self.disc_id)

    async def is_acolyte_owner(self, conn : asyncpg.Connection, a_id : int):
        """Returns true/false depending on whether the acolyte with the given
        ID is in this player's tavern.
        """
        psql = """
                SELECT acolyte_id FROM acolytes
                WHERE user_id = $1 AND acolyte_id = $2;
                """
        val = await conn.fetchval(self.disc_id, a_id)

        return val is not None

    async def equip_acolyte(self, conn : asyncpg.Connection, 
            acolyte_id : int, slot : int):
        """Equips the acolyte with the given ID to the player.
        slot must be an integer 1 or 2.
        """
        if slot not in (1, 2):
            raise Checks.InvalidAcolyteEquip
            # Check this first because its inexpensive and won't waste time

        if not self.is_acolyte_owner(conn, acolyte_id):
            raise Checks.NotAcolyteOwner

        a = acolyte_id == self.acolyte1.acolyte_id
        b = acolyte_id == self.acolyte2.acolyte_id
        if a or b:
            raise Checks.InvalidAcolyteEquip

        if slot == 1:
            self.acolyte1 = get_acolyte_by_id(conn, acolyte_id)
            psql = """
                    UPDATE players
                    SET acolyte1 = $1
                    WHERE user_id = $2;
                    """
        elif slot == 2:
            self.acolyte2 = get_acolyte_by_id(conn, acolyte_id)
            psql = """
                    UPDATE players
                    SET acolyte2 = $1
                    WHERE user_id = $2;
                    """
        
        await conn.execute(psql, acolyte_id, self.disc_id)

    async def unequip_acolyte(self, conn : asyncpg.Connection, slot : int):
        """Removes the acolyte at the given slot of the player.
        slot must be an integer 1 or 2.
        """
        if slot == 1:
            self.acolyte1 = Acolyte()
            psql = "UPDATE players SET acolyte1 = NULL WHERE user_id = $1;"
            await conn.execute(psql, self.disc_id)
        elif slot == 2:
            self.acolyte2 = Acolyte()
            psql = "UPDATE players SET acolyte2 = NULL WHERE user_id = $1;"
            await conn.execute(psql, self.disc_id)
        else:
            raise Checks.InvalidAcolyteEquip

    async def give_gold(self, conn : asyncpg.Connection, gold : int):
        """Gives the player the passed amount of gold."""
        self.gold += gold

        psql = """
                UPDATE players
                SET gold = gold + $1
                WHERE user_id = $2;
                """

        await conn.execute(psql, gold, self.disc_id)

    async def give_rubidics(self, conn : asyncpg.Connection, rubidics : int):
        """Gives the player the passed amount of rubidics."""
        self.rubidics += rubidics

        psql = """
                UPDATE players
                SET rubidics = rubidics + $1
                WHERE user_id = $2;
                """

        await conn.execute(psql, rubidics, self.disc_id)


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


class Acolyte:
    """An acolyte object.

    Attributes
    ----------
    gen_dict : dict
        A dictionary containing the immutable, general information of the
        acolyte with the given name. This information is loaded from json
        and contains the following entries:
        Name, Attack, Scale, Crit, HP, Rarity, Effect, Mat, Story, Image
    acolyte_id : int
        The unique ID of the acolyte
    owner_id : int
        The Discord ID of the owner of this acolyte
    acolyte_name : str
        The name of the acolyte, taken from gen_dict
    xp : int
        The acolyte's experience
    level : int
        The acolyte's level
    dupes : int
        The amount of duplicates this acolyte's owner has

    Methods
    -------
    get_acolyte_by_name(str)
        Retrieves the information of an acolyte with a specific name from
        the json file containing all acolytes and returns it as a dict
    get_level()
        Calculates an acolyte's level using its current xp value
    get_attack()
        Calculates and returns the acolyte's attack stat
    get_crit()
        Calculates and returns the acolyte's crit stat
    get_hp()
        Calculates and returns the acolyte's HP stat
    await add_duplicate()
        Increases the acolyte's dupes value by 1
    """
    def __init__(self, record : asyncpg.Record = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the acolytes table
            Pass nothing to create an empty acolyte
        """
        if record is not None:
            self.gen_dict = self.get_acolyte_by_name(record['acolyte_name'])
            self.acolyte_id = record['acolyte_id']
            self.owner_id = record['user_id']
            self.acolyte_name = record['acolyte_name']
            self.xp = record['xp']
            self.level = self.get_level()
            self.dupes = 10 if record['duplicate'] > 10 else record['duplicate']
            # Having more than 10 dupes has no gameplay effect
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

    @staticmethod
    def get_acolyte_by_name(name : str):
        """
        Returns a dict of the general information of the acolyte.
        Dict: Name, Attack, Scale, Crit, HP, Rarity, Effect, Mat, Story, Image
        """
        with open(config.ACOLYTE_LIST_PATH, 'r') as acolyte_list:
            return json.load(acolyte_list)[name]

    def get_level(self):
        """Returns the acolyte's level."""
        def f(x):
            return int(300 * (x**2))

        level = 0
        while (self.xp >= f(level)):
            level += 1
        level -= 1

        if level > 100:
            level = 100

        return level

    async def check_xp_increase(self, conn : asyncpg.Connection, 
            ctx : discord.context, xp : int):
        """Increases the acolyte's xp by the given amount.
        If the xp increase results in a level-up, prints this out to Discord.        
        """
        old_level = self.level
        self.xp += xp
        psql = """
                UPDATE acolytes
                SET xp = xp + $1
                WHERE acolyte_id = $2;
                """
        await conn.execute(psql, xp, self.acolyte_id)
        self.level = self.get_level()
        if self.level > old_level:
            await ctx.respond(
                f"{self.acolyte_name} levelled up to level {self.level}!")


    def get_attack(self):
        """Returns the acolyte's attack stat."""
        # Duplicates give bonuses depending on acolyte rarity
        if self.gen_dict['Rarity'] == 5:
            attack = self.dupes * 3
        elif self.gen_dict['Rarity'] == 4:
            attack = self.dupes * 2.5
        else:
            attack = self.dupes * 2

        attack += self.gen_dict['Attack']
        attack += self.level * self.gen_dict['Scale']

        return int(attack)

    def get_crit(self):
        """Returns the acolyte's crit stat."""
        crit = self.gen_dict['Crit']
        
        # Duplicates give bonuses depending on acolyte rarity        
        if self.gen_dict['Rarity'] == 5:
            crit += self.dupes
        elif self.gen_dict['Rarity'] == 4:
            crit += self.dupes * .5
        else:
            crit += self.dupes * .2

        return int(crit)

    def get_hp(self):
        """Returns the acolyte's HP stat."""
        hp = self.gen_dict['HP']

        # Duplicates give bonuses depending on acolyte rarity        
        if self.gen_dict['Rarity'] == 5:
            hp += self.dupes * 10
        elif self.gen_dict['Rarity'] == 4:
            hp += self.dupes * 7.5
        else:
            hp += self.dupes * 5

        return int(hp)

    async def add_duplicate(self, conn : asyncpg.Connection):
        """Increments the acolyte's duplicate value by 1"""
        self.dupes += 1

        psql = """
                UPDATE acolytes
                SET duplicate = duplicate + 1
                WHERE acolyte_id = $1
                """

        await conn.execute(psql, self.acolyte_id)


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

async def create_character(conn : asyncpg.Connection, 
        user_id : int, name : str):
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
            WHERE acolyte_id = $1;
            """
    acolyte_record = await conn.fetchrow(psql, acolyte_id)

    return Acolyte(acolyte_id)

async def create_acolyte(conn : asyncpg.Connection, owner_id : int, 
        acolyte : str):
    """Adds a new acolyte with the given name to the passed player.
    If the player already has this acolyte, increment their dupe count.
    Returns the acolyte object in either case
    """
    psql = """
            SELECT acolyte_id 
            FROM acolytes 
            WHERE user_id = $1 AND acolyte_name = $2;
            """

    acolyte_id = await conn.fetchval(psql, owner_id, acolyte)

    if acolyte_id is not None: # Then increment duplicate count
        aco_obj = get_acolyte_by_id(conn, acolyte_id)
        aco_obj.add_duplicate(conn)
        return aco_obj

    else: # Then create a new acolyte and add it to their tavern
        psql = """"
                WITH rows AS (
                    INSERT INTO acolytes (user_id, acolyte_name)
                    VALUES ($1, $2)
                    RETURNING acolyte_id
                )
                SELECT acolyte_id FROM rows;
                """
        acolyte_id = await conn.fetchval(psql, owner_id, acolyte)

        return get_acolyte_by_id(conn, acolyte_id)