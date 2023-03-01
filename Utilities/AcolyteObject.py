import discord

import asyncpg

from copy import deepcopy
from itertools import chain

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
        self._effect_num = None

        # Instance Attributes
        self.id = None
        self.owner_id = None
        self.copies = 0

    @property
    def stars(self) -> str:
        """Returns the acolyte's copy count with a star emoji"""
        return f"{self.copies}★" if self.copies > 0 else "-"

    def get_attack(self) -> int:
        """Returns the acolyte's attack stat."""
        return int(self._attack)

    def get_crit(self) -> int:
        """Returns the acolyte's crit stat."""
        return int(self._crit)

    def get_hp(self) -> int:
        """Returns the acolyte's HP stat."""
        return int(self._hp)
    
    def get_effect_modifier(self, effect_index : int = 0) -> int:
        return 1


class InfoAcolyte(EmptyAcolyte):
    """Acolyte class for read-only purposes. Contains all base acolyte
    information and is not tied to any user or player
    """
    def __init__(self, name : str, info : asyncpg.Record):
        super().__init__()
        # Base Attributes
        self.name = name
        self._attack = info['attack']
        self._crit = info['crit']
        self._hp = info['hp']
        self.effect = info['effect'].replace("{x}", "[{}/{}/{}]")
        self.story = info['story']
        self.image = info['image']
        self._effect_num = info['effect_num']

    @classmethod
    async def from_name(cls, conn : asyncpg.Connection, name : str) -> "InfoAcolyte":
        """Load an acolyte by its name.

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

        if info is None:
            raise Checks.AcolyteDoesNotExist(name)

        cls = cls(name, info)
        
        # Effects have to be generated top-down, but as far as I can tell,
        # I am forced to create these objects in the opposite direction
        # This prevents the effect from being generated before the copies
        # attribute is correctly populated in the case of OwnedAcolyte creation.
        if not isinstance(cls, OwnedAcolyte):
            cls._generate_effect()
        return cls
    
    def _generate_effect(self):
        """Rewrites the effect string into the readable version."""
        self.effect = self.effect.format(*list(chain(*self._effect_num)))


class OwnedAcolyte(InfoAcolyte):
    """An acolyte for player-usage purposes."""

    @classmethod
    async def from_id(cls, conn : asyncpg.Connection, id : int) -> "OwnedAcolyte":
        """Load an acolyte by its ID (an owned instance from the Acolytes table)

        Parameters
        ----------
        conn : asyncpg.Connection
            a connection to the database
        id : int
            the ID of the acolyte being loaded
        """
        psql = """
                SELECT user_id, acolyte_name, copies
                FROM acolytes
                WHERE acolyte_id = $1;
                """  
        info = await conn.fetchrow(psql, id)
        if info is None:
            raise Checks.EmptyObject

        cls = await super().from_name(conn, info['acolyte_name'])
        cls.id = id
        cls.owner_id = info['user_id']
        cls.copies = info['copies']
        cls._generate_effect()
        return cls
    
    @classmethod
    async def from_name(cls, conn : asyncpg.Connection, id : int, name : str) -> "OwnedAcolyte":
        """Load an acolyte by a player's ID and the acolyte's name
        
        Parameters
        ----------
        conn : asyncpg.Connection
            a connection to the database
        id : int
            the ID of the player who owns the acolyte
        name : str
            the name of the acolyte

        Raises
        ------
        Checks.AcolyteNotOwned
            If the player passed does not have any copies of the acolyte
        """
        psql = """
                SELECT acolyte_id, copies
                FROM acolytes
                WHERE user_id = $1 AND acolyte_name = $2;
                """
        info = await conn.fetchrow(psql, id, name)
        if info is None:
            raise Checks.AcolyteNotOwned
        
        cls = await super().from_name(conn, name)
        cls.id = info['acolyte_id']
        cls.owner_id = id
        cls.copies = info['copies']
        cls._generate_effect()
        return cls

    @classmethod
    async def create_acolyte(cls, conn : asyncpg.Connection, owner_id : int, 
            acolyte : str) -> "OwnedAcolyte":
        """Adds a new acolyte with the given name to the passed player.
        If the player already has this acolyte, increment their copies if 
        within range. Returns the acolyte object in all non-error cases.

        Parameters
        ----------
        conn : asyncpg.Connection
            a connection to the database
        owner_id : int
            the discord ID of the owner of the acolyte
        acolyte : str
            the name of the acolyte being created

        Returns
        -------
        OwnedAcolyte
        """
        try:
            current = await OwnedAcolyte.from_name(conn, owner_id, acolyte)
            if current.copies >= 3:
                raise Checks.DuplicateAcolyte(current.id)
            else:
                psql = """
                        UPDATE acolytes
                        SET copies = copies + 1
                        WHERE acolyte_id = $1;
                        """
                await conn.execute(psql, current.id)
                current.copies += 1
                # Run from_name again to regenerate the effect str to reflect
                # the new copy count
                return await OwnedAcolyte.from_name(conn, owner_id, acolyte)

        except Checks.AcolyteNotOwned:
            psql = """
                    INSERT INTO acolytes (user_id, acolyte_name)
                    VALUES ($1, $2);
                    """
            await conn.execute(psql, owner_id, acolyte)
            return await OwnedAcolyte.from_name(conn, owner_id, acolyte)
    
    def _generate_effect(self):
        """Rewrites the effect string into the readable version."""
        index = self.copies - 1
        temp = deepcopy(self._effect_num)
        if index >= 0:
            for subarr in self._effect_num:
                subarr[index] = f"**{subarr[index]}**"
        
        super()._generate_effect()

        self._effect_num = temp # Keep variable as List[List[int]]

    def get_effect_modifier(self, effect_index : int) -> int:
        return self._effect_num[effect_index][self.copies-1]