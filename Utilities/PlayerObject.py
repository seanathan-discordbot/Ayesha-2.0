import discord

import asyncpg

from Utilities import Checks, ItemObject, Vars, AcolyteObject, AssociationObject
from Utilities.ItemObject import Weapon
from Utilities.AcolyteObject import Acolyte
from Utilities.AssociationObject import Association


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
    equipped_item : ItemObject.Weapon
        The weapon object of the item equipped by the player
    acolyte1 : AcolyteObject.Acolyte
        The acolyte object of the acolyte equipped by the player in Slot 1
    acolyte2 : AcolyteObject.Acolyte
        The acolyte object of the acolyte equipped by the player in Slot 2
    assc : AssociationObject.Association
        The association object of the association this player is in
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
        self.equipped_item = record['equipped_item']
        self.acolyte1 = record['acolyte1']
        self.acolyte2 = record['acolyte2']
        self.assc = record['assc']
        self.guild_rank = record['guild_rank']
        self.gold = record['gold']
        self.occupation = record['occupation']
        self.origin = record['origin']
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

    async def _load_equips(self, conn : asyncpg.Connection):
        """Converts object variables from their IDs into the proper objects.
        Run this upon instantiation or else >:(
        """
        self.equipped_item = await ItemObject.get_weapon_by_id(
            conn, self.equipped_item)
        self.acolyte1 = await AcolyteObject.get_acolyte_by_id(
            conn, self.acolyte1)
        self.acolyte2 = await AcolyteObject.get_acolyte_by_id(
            conn, self.acolyte2)
        self.assc = await AssociationObject.get_assc_by_id(conn, self.assc)

    def get_level(self, get_next = False) -> int:
        """Returns the player's level.
        Pass get_next as true to also get the xp needed to level up.
        """
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

        level = level - 1 if level > 0 else 0

        if get_next:
            if level >= 30:
                return level, g(level+1) - self.xp
            else:
                return level, f(level+1) - self.xp
        else:
            return level

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
                color = Vars.ABLUE)
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

    async def set_char_name(self, conn : asyncpg.Connection, name : str):
        """Sets the player's character name. Limit 32 characters."""
        if len(name) > 32:
            raise Checks.ExcessiveCharacterCount(limit=32)
        
        self.char_name = name

        psql = """
                UPDATE players
                SET user_name = $1
                WHERE user_id = $2;
                """
        await conn.execute(psql, name, self.disc_id)

    async def is_weapon_owner(self, conn : asyncpg.Connection, 
            item_id : int) -> bool:
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

        self.equipped_item = ItemObject.get_weapon_by_id(conn, item_id)

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

    async def is_acolyte_owner(self, conn : asyncpg.Connection, 
            a_id : int) -> bool:
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
            self.acolyte1 = AcolyteObject.get_acolyte_by_id(conn, acolyte_id)
            psql = """
                    UPDATE players
                    SET acolyte1 = $1
                    WHERE user_id = $2;
                    """
        elif slot == 2:
            self.acolyte2 = AcolyteObject.get_acolyte_by_id(conn, acolyte_id)
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

    async def join_assc(self, conn : asyncpg.Connection, assc_id : int):
        """Makes the player join the association with the given ID"""
        assc = AssociationObject.get_assc_by_id(conn, assc_id)
        if assc.is_empty:
            raise Checks.InvalidAssociationID
        if assc.get_member_count(conn) >= assc.get_member_capacity():
            raise Checks.AssociationAtCapacity

        psql = """
                UPDATE players
                SET assc = $1, guild_rank = 'Member'
                WHERE user_id = $2;
                """
        await conn.execute(psql, assc_id, self.disc_id)

        self.assc = assc

    async def leave_assc(self, conn : asyncpg.Connection):
        """Makes the player leave their current association."""
        if self.assc.is_empty:
            return

        psql1 = """
                UPDATE players
                SET assc = NULL, guild_rank = NULL
                WHERE user_id = $1;
                """
        psql2 = """
                UPDATE brotherhood_champions
                SET champ1 = NULL
                WHERE champ1 = $1;
                """
        psql3 = """
                UPDATE brotherhood_champions
                SET champ2 = NULL
                WHERE champ2 = $1;
                """
        psql4 = """
                UPDATE brotherhood_champions
                SET champ3 = NULL
                WHERE champ3 = $1;
                """

        await conn.execute(psql1, self.disc_id)
        await conn.execute(psql2, self.disc_id)
        await conn.execute(psql3, self.disc_id)
        await conn.execute(psql4, self.disc_id)

        self.assc = Association()

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

    def get_attack(self) -> int:
        """Returns the player's attack stat, calculated from all other sources.
        The value returned by this method is 'the final say' on the stat.
        """
        attack = 10 + int(self.level / 3)
        attack += self.equipped_item.attack
        attack += self.acolyte1.get_attack()
        attack += self.acolyte2.get_attack()
        valid_weapons = Vars.OCCUPATIONS[self.occupation]['weapon_bonus']
        if self.equipped_item.type in valid_weapons:
            attack += 20
        attack += Vars.ORIGINS[self.origin]['atk_bonus']
        if self.assc.type == "Brotherhood":
            lvl = self.assc.get_level()
            attack += int(lvl * (lvl + 1) / 4)
        attack += Vars.OCCUPATIONS[self.occupation]['atk_bonus']
        attack = int(attack * 1.1) if self.occupation == "Soldier" else attack
        # TODO implement comptroller bonus

        return attack

    def get_crit(self) -> int:
        """Returns the player's crit stat, calculated from all other sources.
        The value returned by this method is 'the final say' on the stat.
        """
        crit = 5
        crit += self.equipped_item.crit
        crit += self.acolyte1.get_crit()
        crit += self.acolyte2.get_crit()
        crit += Vars.ORIGINS[self.origin]['crit_bonus']
        if self.assc.type == "Brotherhood":
            crit += self.assc.get_level()
        crit += Vars.OCCUPATIONS[self.occupation]['crit_bonus']
        # TODO implement comptroller bonus

        return crit

    def get_hp(self) -> int:
        """Returns the player's HP stat, calculated from all other sources.
        The value returned by this method is 'the final say' on the stat.
        """
        hp = 500 + self.level
        hp += self.acolyte1.get_hp()
        hp += self.acolyte2.get_hp()
        hp += Vars.ORIGINS[self.origin]['hp_bonus']
        hp += Vars.OCCUPATIONS[self.occupation]['hp_bonus']
        # TODO implement comptroller bonus

        return hp        


async def get_player_by_id(conn : asyncpg.Connection, user_id : int) -> Player:
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
                origin,
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

    if player_record is None:
        raise Checks.PlayerHasNoChar

    player = Player(player_record)
    await player._load_equips(conn)

    return player

async def create_character(conn : asyncpg.Connection, user_id : int, 
        name : str) -> Player:
    """Creates and returns a profile for the user with the given Discord ID."""
    psql1 = "INSERT INTO players (user_id, user_name) VALUES ($1, $2);"
    psql2 = "INSERT INTO resources (user_id) VALUES ($1);"
    psql3 = "INSERT INTO strategy (user_id) VALUES ($1);"
    await conn.execute(psql1, user_id, name)
    await conn.execute(psql2, user_id)
    await conn.execute(psql3, user_id)

    await ItemObject.create_weapon(
        conn, user_id, "Common", attack=20, crit=0, weapon_name="Wooden Spear", 
        weapon_type="Spear")

    return await get_player_by_id(conn, user_id)