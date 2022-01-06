import discord

from discord.ext import commands

class HasChar(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class CurrentlyTraveling(commands.CheckFailure):
    def __init__(self, adv, dest, *args, **kwargs):
        self.adv = adv
        self.dest = dest
        super().__init__(*args, **kwargs)

class NotCurrentlyTraveling(commands.CheckFailure):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ExcessiveCharacterCount(Exception):
    def __init__(self, limit : int):
        self.limit = limit

class PlayerHasNoChar(commands.MemberNotFound):
    def __init__(self):
        self.message = "Player has no char."
        super().__init__(self.message)

class NotInAssociation(commands.CheckFailure):
    def __init__(self, req : str = None, current : str = None, *args, **kwargs):
        """General exception for a player not being in an association
        or being in an association of the wrong type. 
        Pass nothing if this error is being raised because player is not in any
        association, else pass the req and current as needed.
        """
        self.req = req
        self.current = current
        super().__init__(*args, **kwargs)

class InAssociation(commands.CheckFailure):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class IncorrectAssociationRank(commands.CheckFailure):
    def __init__(self, rank : str, *args, **kwargs):
        self.rank = rank
        super().__init__(*args, **kwargs)

class EmptyObject(Exception):
    pass

class NotWeaponOwner(Exception):
    pass

class InvalidWeaponType(Exception):
    pass

class NotArmorOwner(Exception):
    pass

class InvalidArmorType(Exception):
    pass

class InvalidArmorMaterial(Exception):
    pass

class InvalidAccessoryPrefix(Exception):
    pass

class InvalidAccessoryMaterial(Exception):
    pass

class InvalidResource(Exception):
    def __init__(self, resource : str):
        self.resource = resource

class NotAcolyteOwner(Exception):
    pass

class InvalidAcolyteEquip(Exception):
    pass

class InvalidAssociationID(Exception):
    pass

class AssociationAtCapacity(Exception):
    pass

class NotInSpecifiedAssociation(Exception):
    def __init__(self, type : str):
        self.type = type

class PlayerNotInSpecifiedAssociation(Exception):
    def __init__(self, type : str):
        self.type = type

class PlayerAlreadyChampion(Exception):
    pass

class NotEnoughGold(Exception):
    def __init__(self, needed : int, current : int):
        self.diff = needed - current

class NotEnoughResources(Exception):
    def __init__(self, resource : str, needed : int, current : int):
        self.resource = resource
        self.diff = needed - current
        super().__init__(needed, current)

class InvalidTransactionType(Exception):
    pass

class InvalidOccupation(Exception):
    def __init__(self, occupation : str):
        self.occupation = occupation

class InvalidOrigin(Exception):
    def __init__(self, origin : str):
        self.origin = origin

class NameTaken(Exception):
    def __init__(self, name : str):
        self.name = name

class InvalidIconURL(Exception):
    pass

class InvalidRankName(Exception):
    def __init__(self, rank : str):
        self.rank = rank

# --- NOW FOR THE ACTUAL CHECKS :) ---

async def not_player(ctx):
    async with ctx.bot.db.acquire() as conn:
        psql = """
                SELECT user_id
                FROM players
                WHERE user_id = $1;
                """
        result = await conn.fetchval(psql, ctx.author.id)
        
    if result is None:
        return True
    raise HasChar(ctx.author, 
        message='Player has a character and failed not_player check.')

async def is_player(ctx):
    async with ctx.bot.db.acquire() as conn:
        psql = """
                SELECT user_id
                FROM players
                WHERE user_id = $1;
                """
        result = await conn.fetchval(psql, ctx.author.id)

    if result is None:
        raise PlayerHasNoChar
    return True

async def is_not_travelling(ctx):
    async with ctx.bot.db.acquire() as conn:
        psql = """
                SELECT adventure, destination
                FROM players
                WHERE user_id = $1;
                """
        result = await conn.fetchrow(psql, ctx.author.id)

    if result['adventure'] is None:
        return True
    raise CurrentlyTraveling(result['adventure'], result['destination'])

async def is_travelling(ctx):
    async with ctx.bot.db.acquire() as conn:
        psql = """
                SELECT adventure
                FROM players
                WHERE user_id = $1;
                """
        result = await conn.fetchval(psql, ctx.author.id)

    if result is None:
        raise NotCurrentlyTraveling
    return True

# Auxiliary function - don't use in commands
async def _get_assc(ctx):
    async with ctx.bot.db.acquire() as conn:
        psql = """
                SELECT players.assc, associations.assc_type
                FROM players
                LEFT JOIN associations
                    ON players.assc = associations.assc_id
                WHERE user_id = $1;
                """
        return await conn.fetchrow(psql, ctx.author.id)

async def in_association(ctx):
    record = await _get_assc(ctx)
    if record['assc'] is None:
        raise NotInAssociation
    return True

async def not_in_association(ctx):
    record = await _get_assc(ctx)
    if record['assc'] is not None:
        raise InAssociation
    return True

async def in_brotherhood(ctx):
    record = await _get_assc(ctx)
    try:
        if record['assc_type'] == "Brotherhood":
            return True
    except TypeError:
        raise NotInAssociation("Brotherhood")
    raise NotInAssociation("Brotherhood", record['assc_type'])

async def in_college(ctx):
    record = await _get_assc(ctx)
    try:
        if record['assc_type'] == "College":
            return True
    except TypeError:
        raise NotInAssociation("College")
    raise NotInAssociation("College", record['assc_type'])

async def in_guild(ctx):
    record = await _get_assc(ctx)
    try:
        if record['assc_type'] == "Guild":
            return True
    except TypeError:
        raise NotInAssociation("Guild")
    raise NotInAssociation("Guild", record['assc_type'])

async def is_assc_leader(ctx):
    psql = """
            SELECT guild_rank 
            FROM players
            WHERE user_id = $1;
            """
    async with ctx.bot.db.acquire() as conn:
        rank = await conn.fetchval(psql, ctx.author.id)
    if rank != "Leader":
        raise IncorrectAssociationRank("Leader")
    return True

async def is_assc_officer(ctx):
    psql = """
            SELECT guild_rank 
            FROM players
            WHERE user_id = $1;
            """
    async with ctx.bot.db.acquire() as conn:
        rank = await conn.fetchval(psql, ctx.author.id)
    if rank not in ("Leader", "Officer"):
        raise IncorrectAssociationRank("Officer")
    return True