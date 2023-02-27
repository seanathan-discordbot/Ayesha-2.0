import discord

import asyncpg

from Utilities import Checks

class EmptyAcolyte: # TODO: change to 'Acolyte'
    """Empty acolyte for placeholding purposes. It is convenient for the bot
    to assume that a player or some other agent always has an acolyte equipped,
    so this class creates an empty dummy object with all the attributes of the
    `OwnedAcolyte` for similar read-only functionality.
    """
    def __init__(self):
        # Base Attributes
        self.name = None
        self._attack = 0
        self._crit = 0
        self._hp = 0
        self.effect = None
        self.story = None
        self.image = None

        # Instance Attributes
        self.id = None
        self.owner_id = None
        self.copies = 0

    def get_attack(self) -> int:
        """Returns the acolyte's attack stat."""
        return int(self._attack)

    def get_crit(self) -> int:
        """Returns the acolyte's crit stat."""
        return int(self._crit)

    def get_hp(self) -> int:
        """Returns the acolyte's HP stat."""
        return int(self._hp)


class InfoAcolyte(EmptyAcolyte):
    """Acolyte used for read-only information and not tied to any user."""
    def __init__(self, name : str, info : asyncpg.Record):
        super().__init__()
        # Base Attributes
        self.name = name
        self._attack = info['attack']
        self._crit = info['crit']
        self._hp = info['hp']
        self.effect = info['effect']
        self.story = info['story']
        self.image = info['image']

    @classmethod
    async def from_name(cls, conn : asyncpg.Connection, name : str) -> \
            "InfoAcolyte":
        """Acolyte class for read-only purposes. Contains all base acolyte
        information and is not tied to any user or player

        Parameters
        ----------
        conn : asyncpg.Connection
            a connection to the database
        name : str
            the name of the acolyte being created

        Returns
        -------
        InfoAcolyte
        """        
        psql = """
                SELECT attack, crit, hp, effect, story, image, effect_num
                FROM acolyte_list
                WHERE name = $1;
                """
        info = await conn.fetchrow(psql, name)

        return cls(name, info)


class OwnedAcolyte(InfoAcolyte):
    pass


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
    """
    def __init__(self, record : asyncpg.Record = None, base_info : dict = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the acolytes table
            Pass nothing to create an empty acolyte
        """
        invalid_argument1 = record is None and base_info is not None
        invalid_argument2 = record is not None and base_info is None
        if invalid_argument1 or invalid_argument2:
            raise discord.InvalidArgument

        if record is not None:
            self.is_empty = False
            self.gen_dict = base_info.copy() # unsure if copy is necessary
            self.acolyte_id = record['acolyte_id']
            self.owner_id = record['user_id']
            self.acolyte_name = record['acolyte_name']
            self.copies = record['copies']
        else:
            self.is_empty = True
            self.gen_dict = {
                'Name' : None,
                'Attack' : 0,
                'Crit' : 0,
                'HP' : 0,
                'Effect' : None,
                'Story' : None,
                'Image' : None
            }
            self.acolyte_id = None
            self.owner_id = None
            self.acolyte_name = None
            self.copies = 0

    @staticmethod
    async def get_acolyte_by_name(name : str, conn : asyncpg.Connection) -> dict:
        """
        Returns a dict of the general information of the acolyte.
        Dict: Name, Attack, Crit, HP, Rarity, Effect, Story, Image
        """
        psql = """
                SELECT 
                    attack, crit, hp, effect, story, image
                FROM acolyte_list
                WHERE name = $1;
                """
        acolyte = await conn.fetchrow(psql, name)
        return {
            "Name" : name,
            "Attack" : acolyte['attack'],
            "Crit" : acolyte['crit'],
            "HP" : acolyte['hp'],
            "Effect" : acolyte['effect'],
            "Story" : acolyte['story'],
            "Image" : acolyte['image']
        }

    def get_attack(self) -> int:
        """Returns the acolyte's attack stat."""
        return int(self.gen_dict['Attack'])

    def get_crit(self) -> int:
        """Returns the acolyte's crit stat."""
        return int(self.gen_dict['Crit'])

    def get_hp(self) -> int:
        """Returns the acolyte's HP stat."""
        return int(self.gen_dict['HP'])


async def get_acolyte_by_id(conn : asyncpg.Connection, 
        acolyte_id : int) -> Acolyte:
    """Return an acolyte object of the acolyte with the given ID."""
    psql = """
            SELECT acolyte_id, user_id, acolyte_name, copies
            FROM acolytes
            WHERE acolyte_id = $1;
            """
    acolyte_record = await conn.fetchrow(psql, acolyte_id)
    if acolyte_record is None:
        return Acolyte(None, None) # Creates an empty acolyte object

    base_info = await Acolyte.get_acolyte_by_name(
        acolyte_record['acolyte_name'], conn)

    return Acolyte(acolyte_record, base_info)

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

    original_id = await conn.fetchval(psql, owner_id, acolyte)
    if original_id is not None:
        raise Checks.DuplicateAcolyte(original_id)

    else: # Then create a new acolyte and add it to their tavern
        psql = """
                WITH rows AS (
                    INSERT INTO acolytes (user_id, acolyte_name)
                    VALUES ($1, $2)
                    RETURNING acolyte_id
                )
                SELECT acolyte_id FROM rows;
                """
        acolyte_id = await conn.fetchval(psql, owner_id, acolyte)

        return await get_acolyte_by_id(conn, acolyte_id)