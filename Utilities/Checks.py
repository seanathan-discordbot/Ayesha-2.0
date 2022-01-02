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