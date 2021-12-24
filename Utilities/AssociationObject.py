import discord

import asyncpg

from Utilities import Checks, Vars


class Association:
    """The association (guild/brotherhood/college) object

    Attributes
    ----------
    id : int
        The unique ID of the association
    name : str
        The unique name of the association
    type : str
        The type of association (Brotherhood/Guild/College)
    xp : int
        The xp of the association
    leader : int
        The discord ID of the association leader
    desc : str
        The description text of the association
    icon : str
        The link to the icon of the association (not necessarily valid)
    join_status : str
        Whether the association is "open" or "closed" to new members via the
        join command
    base : Optional[str]
        The area of the map that the association is based in
    base_set : bool
        Whether the association's base has been set by the leader
    lvl_req = int
        The minimum level for players to join via the join command

    Methods
    -------
    
    """
    def __init__(self, record : asyncpg.Record = None):
        """
        Parameters
        ----------
        Optional[record] : asyncpg.Record
            A record containing information from the associations table
            Pass nothing to create an empty association
        """
        if record is not None:
            self.id = record['assc_id']
            self.name = record['assc_name']
            self.type = record['ascc_type']
            self.xp = record['assc_xp']
            self.leader = record['leader_id']
            self.desc = record['desc']
            self.icon = record['assc_icon']
            self.join_status = record['join_status']
            self.base = record['base']
            self.base_set = record['base_set']
            self.lvl_req = record['min_level']
        else:
            self.id = None
            self.name = None
            self.type = None
            self.xp = 0
            self.leader = None
            self.desc = None
            self.icon = None
            self.join_status = "closed"
            self.base = None
            self.base_set = True
            self.lvl_req = 0

    def get_level(self):
        """Returns the level of the guild. Each level is 1,000,000 xp."""
        return int(self.xp / 1000000) if int(self.xp / 1000000) < 10 else 10

    def get_member_capacity(self):
        """Returns the member capacity of the association. 
        Default is 30, +2 for each level, up to 50 at level 10
        """
        return 30 + self.get_level() * 2

    async def get_member_count(self, conn : asyncpg.Connection):
        """Returns the amount of players in this association"""
        psql = """
                SELECT member_count
                FROM guild_membercount
                WHERE guild_id = $1;
                """
        return await conn.fetchval(psql, self.id)

    async def increase_xp(self, conn : asyncpg.Connection, xp : int):
        """Increase the association's xp by the given amount."""
        self.xp += xp

        psql = """
                UPDATE associations
                SET assc_xp = assc_xp + $1
                WHERE assc_id = $2;
                """

        await conn.execute(psql, xp, self.id)

    async def set_description(self, conn : asyncpg.Connection, desc : str):
        """Set the description of the association. Max 256 characters."""
        if len(desc) > 256:
            raise Checks.ExcessiveCharacterCount(256)

        self.desc = desc

        psql = """
                UPDATE associations
                SET assc_desc = $1
                WHERE assc_id = $2
                """

        await conn.execute(psql, desc, self.id)

    async def set_icon(self, conn : asyncpg.Connection, icon : str):
        """Set the icon of the association. Please give a valid link."""
        self.desc = icon

        psql = """
                UPDATE associations
                SET assc_icon = $1
                WHERE assc_id = $2
                """

        await conn.execute(psql, icon, self.id)

    async def lock(self, conn : asyncpg.Connection):
        """Set the lock-status of the association to closed."""
        self.join_status = "closed"
        psql = """
                UPDATE associations 
                SET join_status = 'closed' 
                WHERE guild_id = $1
                """
        await conn.execute(psql, self.id)

    async def unlock(self, conn : asyncpg.Connection):
        """Set the lock-status of the association to open."""
        self.join_status = "open"
        psql = """
                UPDATE associations 
                SET join_status = 'open' 
                WHERE guild_id = $1
                """
        await conn.execute(psql, self.id)

    # TODO implement destroy() and set_leader()
    # TODO implement join and leave commands for players
    # TODO implement functionality for each association type
    # TODO document
        

    async def set_assc_lvl_req(self, conn : asyncpg.Connection, level : int):
        """Sets the minimum level requirement for new members to join via
        the join command.
        """
        if level < 0 or level > 250:
            raise discord.InvalidArgument

        self.lvl_req = level

        psql = """
                UPDATE associations
                SET min_level = $1
                WHERE assc_id = $2;
                """
        await conn.execute(psql, level, self.id)


async def get_assc_by_id(conn : asyncpg.Connection, assc_id : int):
    """Return an association object of the association with the given ID."""
    psql = """
            SELECT 
                assc_id, assc_name, assc_type, assc_xp, leader_id, assc_desc,
                assc_icon, join_status, base, base_set, min_level
            FROM associations
            WHERE assc_id = $1;
            """
    assc_record = await conn.fetchrow(psql, assc_id)

    return Association(assc_record)

async def get_assc_by_name(conn : asyncpg.Connection, assc_name : str):
    """Retrun an association object of the association with the given name."""
    psql = "SELECT assc_id FROM associations WHERE assc_name = $1;"
    assc_id = await conn.fetchval(psql, assc_name)
    return get_assc_by_id(assc_id)