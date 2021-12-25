import discord

from discord.ext import commands

class HasChar(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
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