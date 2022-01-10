import discord

import aiohttp
import asyncpg

from Utilities import Checks, Vars


class Association:
    """The association (guild/brotherhood/college) object. Changing the object
    attributes are not permanent but siotable for cases in which temporary
    changes can be advantageous in some commands. Generally, the async-methods
    will make changes to the database.

    It is convenient for the bot to assume that a player always is in an 
    association, so this class can create empty objects by not passing a record
    upon instantiation. If a command alters the object's database value, it will
    first check the is_empty attribute to ensure that such a change is possible.
    Changing an empty object will result in an EmptyObject Exception.

    Attributes
    ----------
    is_empty : bool
        Whether this object is a dummy object or not
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
            self.is_empty = False
            self.id = record['assc_id']
            self.name = record['assc_name']
            self.type = record['assc_type']
            self.xp = record['assc_xp']
            self.leader = record['leader_id']
            self.desc = record['assc_desc']
            self.icon = record['assc_icon']
            self.join_status = record['join_status']
            self.base = record['base']
            self.base_set = record['base_set']
            self.lvl_req = record['min_level']
        else:
            self.is_empty = True
            self.id = None
            self.name = None
            self.type = "None"
            self.xp = 0
            self.leader = None
            self.desc = None
            self.icon = None
            self.join_status = "closed"
            self.base = None
            self.base_set = True
            self.lvl_req = 0

    def get_level(self, give_graphic = False) -> int:
        """Returns the level of the guild. Each level is 1,000,000 xp."""
        level = int(self.xp / 1000000) if int(self.xp / 1000000) < 10 else 10

        if give_graphic:
            dashes = ["".join(["▬"]*i) for i in range(10)]
            progress = int((self.xp % 1000000) / 100000)
            graphic = dashes[progress]+'◆'+dashes[9-progress]
            return level, graphic
        else:
            return level

    def get_member_capacity(self) -> int:
        """Returns the member capacity of the association. 
        Default is 30, +2 for each level, up to 50 at level 10
        """
        return 30 + self.get_level() * 2

    async def get_member_count(self, conn : asyncpg.Connection) -> int:
        """Returns the amount of players in this association"""
        if self.is_empty:
            raise Checks.EmptyObject
        
        psql = """
                SELECT member_count
                FROM guild_membercount
                WHERE guild_id = $1;
                """
        return await conn.fetchval(psql, self.id)

    async def get_all_members(self, conn : asyncpg.Connection) -> list:
        """Returns a list of 'PlayerObject.Player's for every assc member.
        Using ctx.defer() in any command that invokes this method may be 
        a good idea.
        """
        psql = """
                SELECT user_id
                FROM players
                WHERE assc = $1;
                """
        members = await conn.fetch(psql, self.id)
        from Utilities.PlayerObject import get_player_by_id as gpbi
        return [await gpbi(conn, id['user_id']) for id in members]

    async def increase_xp(self, conn : asyncpg.Connection, xp : int):
        """Increase the association's xp by the given amount."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        self.xp += xp

        psql = """
                UPDATE associations
                SET assc_xp = assc_xp + $1
                WHERE assc_id = $2;
                """

        await conn.execute(psql, xp, self.id)

    async def set_description(self, conn : asyncpg.Connection, desc : str):
        """Set the description of the association. Max 256 characters."""
        if self.is_empty:
            raise Checks.EmptyObject
        
        if len(desc) > 256:
            raise Checks.ExcessiveCharacterCount(256)

        self.desc = desc

        psql = """
                UPDATE associations
                SET assc_desc = $1
                WHERE assc_id = $2;
                """

        await conn.execute(psql, desc, self.id)

    async def set_icon(self, conn : asyncpg.Connection, icon : str):
        """Set the icon of the association. Please give a valid link."""
        if self.is_empty:
            raise Checks.EmptyObject
        async with aiohttp.ClientSession() as client:
            resp = await client.get(icon)
            img = resp.headers.get("content-type")
            if img not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
                raise Checks.InvalidIconURL
        self.desc = icon
        psql = """
                UPDATE associations
                SET assc_icon = $1
                WHERE assc_id = $2;
                """

        await conn.execute(psql, icon, self.id)

    async def lock(self, conn : asyncpg.Connection):
        if self.is_empty:
            raise Checks.EmptyObject
        
        """Set the lock-status of the association to closed."""
        self.join_status = "closed"
        psql = """
                UPDATE associations 
                SET join_status = 'closed' 
                WHERE assc_id = $1;
                """
        await conn.execute(psql, self.id)

    async def unlock(self, conn : asyncpg.Connection):
        if self.is_empty:
            raise Checks.EmptyObject
        
        """Set the lock-status of the association to open."""
        self.join_status = "open"
        psql = """
                UPDATE associations 
                SET join_status = 'open' 
                WHERE assc_id = $1;
                """
        await conn.execute(psql, self.id)

    async def set_leader(self, conn : asyncpg.Connection, leader_id : int):
        """Replaces the guild leader."""
        if self.is_empty:
            raise Checks.EmptyObject

        psql1 = """
                UPDATE players
                SET guild_rank = 'Officer'
                WHERE user_id = $1;
                """
        psql2 = """
                UPDATE players
                SET guild_rank = 'Leader'
                WHERE user_id = $1;
                """
        psql3 = """
                UPDATE associations
                SET leader_id = $1
                WHERE assc_id = $2;
                """
        await conn.execute(psql1, self.leader)
        await conn.execute(psql2, leader_id)
        await conn.execute(psql3, leader_id, self.id)        
        
        self.leader = leader_id

    async def destroy(self, conn : asyncpg.Connection):
        """Disbands the association.
        Associations are not deleted, but set in such a way that there are no
        members and cannot be joined.
        """
        if self.is_empty:
            raise Checks.EmptyObject

        psql1 = """
                UPDATE associations
                SET 
                    leader_id = 767234703161294858,
                    assc_desc = 'This association has been disbanded.',
                    join_status = 'closed'
                WHERE assc_id = $1;
                """
        psql2 = """
                UPDATE players 
                SET assc = NULL, guild_rank = NULL
                WHERE assc = $1;
                """
        psql3 = """
                WITH balance AS (
                    DELETE FROM guild_bank_account
                    WHERE user_id = $1
                    RETURNING account_funds
                )
                SELECT account_funds 
                FROM balance;
                """
        psql4 = """
                UPDATE players
                SET gold = gold + $1
                WHERE user_id = $2;
                """

        await conn.execute(psql1, self.id)
        await conn.execute(psql2, self.id)

        # Brotherhood champion deletion is probably unneccessary
        if self.type == "Guild":
            in_bank = await conn.fetchval(psql3, self.leader)
            if in_bank is not None:
                await conn.execute(psql4, in_bank, self.leader)

        self = Association()
        

    async def set_assc_lvl_req(self, conn : asyncpg.Connection, level : int):
        """Sets the minimum level requirement for new members to join via
        the join command.
        """
        if self.is_empty:
            raise Checks.EmptyObject

        if level < 0 or level > 250:
            raise discord.InvalidArgument

        self.lvl_req = level

        psql = """
                UPDATE associations
                SET min_level = $1
                WHERE assc_id = $2;
                """
        await conn.execute(psql, level, self.id)

    # Since knowing an association's ID or name does not guarantee knowing
    # its type, subclassing the different types is not advantageous.
    # Each method will first check to see if the type is compatible.

    # --- BROTHERHOOD METHODS ---
    async def get_champions(self, conn : asyncpg.Connection) -> list:
        """Returns a list of 'Player's containing the brotherhood's champions.
        
        If the brotherhood has less than the 3 maximum champions, the empty
        slots will be None. Note the possibility of an AttributeError when 
        working with the list.        
        """
        if self.type != "Brotherhood":
            raise Checks.NotInSpecifiedAssociation("Brotherhood")

        from Utilities.PlayerObject import get_player_by_id # evil emoji

        psql = """
                SELECT champ1, champ2, champ3
                FROM brotherhood_champions
                WHERE assc_id = $1;
                """
        champs = await conn.fetchrow(psql, self.id)
        champ_list = [None, None, None]
        if champs['champ1'] is not None:
            champ_list[0] = await get_player_by_id(conn, champs['champ1'])
        if champs['champ2'] is not None:
            champ_list[1] = await get_player_by_id(conn, champs['champ2'])
        if champs['champ3'] is not None:
            champ_list[2] = await get_player_by_id(conn, champs['champ3'])      

        return champ_list

    async def set_champion(self, conn : asyncpg.Connection, player_id : int, 
            slot : int):
        """Update the ID of a brotherhood champion. 
        Slot must be an integer 1-3."""
        if self.type != "Brotherhood":
            raise Checks.NotInSpecifiedAssociation("Brotherhood")

        from Utilities.PlayerObject import get_player_by_id

        player = await get_player_by_id(conn, player_id)
        if player.assc.id != self.id:
            raise Checks.PlayerNotInSpecifiedAssociation("Brotherhood")

        current = await self.get_champions(conn)
        current_ids = []
        for champ in current:
            try:
                current_ids.append(champ.disc_id)
            except AttributeError: # no champion, so no disc ID
                pass
        if player.disc_id in current_ids:
            raise Checks.PlayerAlreadyChampion

        if slot == 1:
            psql = """
                    UPDATE brotherhood_champions
                    SET champ1 = $1
                    WHERE assc_id = $2;
                    """
        elif slot == 2:
            psql = """
                    UPDATE brotherhood_champions
                    SET champ1 = $1
                    WHERE assc_id = $2;
                    """
        elif slot == 3:
            psql = """
                    UPDATE brotherhood_champions
                    SET champ1 = $1
                    WHERE assc_id = $2;
                    """
        else:
            raise discord.InvalidArgument

        await conn.execute(psql, player.disc_id, self.id)

    async def remove_champion(self, conn : asyncpg.Connection, slot : int):
        """Remove the champion in the given slot, which is an int 1-3."""
        if self.type != "Brotherhood":
            raise Checks.NotInSpecifiedAssociation("Brotherhood")

        if slot == 1:
            psql = """
                    UPDATE brotherhood_champions
                    SET champ1 = NULL
                    WHERE assc_id = $1;
                    """
        elif slot == 2:
            psql = """
                    UPDATE brotherhood_champions
                    SET champ1 = NULL
                    WHERE assc_id = $1;
                    """
        elif slot == 3:
            psql = """
                    UPDATE brotherhood_champions
                    SET champ1 = NULL
                    WHERE assc_id = $1;
                    """
        else:
            raise discord.InvalidArgument

        await conn.execute(psql, self.id)

    async def set_territory_controller(self, conn : asyncpg.Connection, 
            area : str):
        """Sets the guild to be the controller of the given territory."""
        psql = """
                INSERT INTO area_control (area, owner)
                VALUES ($1, $2);
                """
        await conn.execute(psql, area, self.id)


async def get_assc_by_id(conn : asyncpg.Connection, 
        assc_id : int) -> Association:
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

async def get_assc_by_name(conn : asyncpg.Connection, 
        assc_name : str) -> Association:
    """Retrun an association object of the association with the given name."""
    psql = "SELECT assc_id FROM associations WHERE assc_name = $1;"
    assc_id = await conn.fetchval(psql, assc_name)
    return get_assc_by_id(assc_id)

async def create_assc(conn : asyncpg.Connection, name : str, type : str, 
        base : str, leader : int) -> Association:
    """Create an association with the fields given.
    type must be 'Brotherhood','College', or 'Guild'.
    """
    psql = """
            SELECT assc_id 
            FROM associations
            WHERE assc_name = $1;
            """
    if await conn.fetchval(psql, name) is not None:
        raise Checks.NameTaken(name)
    psql1 = """
            WITH rows AS (
                INSERT INTO associations
                    (assc_name, assc_type, leader_id, assc_icon, base)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING assc_id
            )
            SELECT assc_id FROM rows;
            """
    psql2 = """
            UPDATE players
            SET assc = $1, guild_rank = 'Leader'
            WHERE user_id = $2;
            """
    psql3 = """
            INSERT INTO brotherhood_champions (assc_id)
            VALUES ($1);
            """
    assc_id = await conn.fetchval(
        psql1, name, type, leader, Vars.DEFAULT_ICON, base)
    await conn.execute(psql2, assc_id, leader)
    if type == "Brotherhood":
        await conn.execute(psql3, assc_id)
    return await get_assc_by_id(conn, assc_id)

async def get_territory_controller(conn : asyncpg.Connection, area : str):
    """Returns the Association object of the brotherhood in control of 
    the given area.
    """
    psql = """
            SELECT owner
            FROM area_control
            WHERE area = $1
            ORDER BY id DESC
            LIMIT 1;
            """
    return await get_assc_by_id(conn, await conn.fetchval(psql, area))