

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