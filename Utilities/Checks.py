

class ExcessiveCharacterCount(Exception):
    def __init__(self, limit : int):
        self.limit = limit

class NotWeaponOwner(Exception):
    pass