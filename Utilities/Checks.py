

class ExcessiveCharacterCount(Exception):
    def __init__(self, limit : int):
        self.limit = limit

class EmptyObject(Exception):
    pass

class NotWeaponOwner(Exception):
    pass

class NotAcolyteOwner(Exception):
    pass

class InvalidAcolyteEquip(Exception):
    pass