import discord

import asyncpg
import coolname

import json
import random

from Utilities import Checks, Vars

class Acolyte:
    """An acolyte object. Changing the object attributes are not permanent,
    and are suitable for cases in which temporary changes can be advantageous
    for use in some commands. Only changes made by the set-methods will be
    committed into the database.

    It is convenient for the bot to assume that a player always has an acolyte
    equipped, so this class can create empty objects by not passing a record
    upon instantiation. If a command alters the object's database value, it
    will first check the is_empty attribute to ensure such a change is possible.
    Changing an empty object will result in an EmptyObject exception.

    Attributes
    ----------
    is_empty : bool
        Whether this object is a dummy object or not
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
    check_xp_increase()
        Increase the acolyte's xp by the given amount and checks for levelups.
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
            self.is_empty = False
            self.gen_dict = self.get_acolyte_by_name(record['acolyte_name'])
            self.acolyte_id = record['acolyte_id']
            self.owner_id = record['user_id']
            self.acolyte_name = record['acolyte_name']
            self.xp = record['xp']
            self.level = self.get_level()
            self.dupes = 10 if record['duplicate'] > 10 else record['duplicate']
            # Having more than 10 dupes has no gameplay effect
        else:
            self.is_empty = True
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
    def get_acolyte_by_name(name : str) -> dict:
        """
        Returns a dict of the general information of the acolyte.
        Dict: Name, Attack, Scale, Crit, HP, Rarity, Effect, Mat, Story, Image
        """
        with open(Vars.ACOLYTE_LIST_PATH, 'r') as acolyte_list:
            return json.load(acolyte_list)[name]

    def get_level(self) -> int:
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
        if self.is_empty:
            raise Checks.EmptyObject

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


    def get_attack(self) -> int:
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

    def get_crit(self) -> int:
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

    def get_hp(self) -> int:
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
        if self.is_empty:
            raise Checks.EmptyObject   

        self.dupes += 1

        psql = """
                UPDATE acolytes
                SET duplicate = duplicate + 1
                WHERE acolyte_id = $1
                """

        await conn.execute(psql, self.acolyte_id)


async def get_acolyte_by_id(conn : asyncpg.Connection, 
        acolyte_id : int) -> Acolyte:
    """Return an acolyte object of the acolyte with the given ID."""
    psql = """
            SELECT acolyte_id, user_id, acolyte_name, xp, duplicate
            FROM acolytes
            WHERE acolyte_id = $1;
            """
    acolyte_record = await conn.fetchrow(psql, acolyte_id)

    return Acolyte(acolyte_id)

async def create_acolyte(conn : asyncpg.Connection, owner_id : int, 
        acolyte : str) -> Acolyte:
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