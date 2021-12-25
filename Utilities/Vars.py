ACOLYTE_LIST_PATH = r'F:\OneDrive\Python_Projects\Ayesha_Rewrite\Assets\Acolyte_List.json'

ABLUE =  0xBEDCF6

OCCUPATIONS = {
    'Soldier' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Spear", "Sword")
    },
    'Blacksmith' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Greatsword", "Gauntlets")
    },
    'Farmer' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Sling", "Falx")
    },
    'Hunter' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Bow", "Javelin")
    },
    'Merchant' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Dagger", "Mace")
    },
    'Traveler' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Staff", "Javelin")
    },
    'Leatherworker' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 250,
        'weapon_bonus' : ("Mace", "Axe")
    },
    'Butcher' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Axe", "Dagger")
    },
    'Engineer' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Trebuchet", "Falx")
    },
    'Scribe' : {
        'atk_bonus' : 0,
        'crit_bonus' : 10,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Sword", "Dagger")
    },
    None : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : []
    }
}

ORIGINS = {
    'Riverburn' : {
        'atk_bonus' : 5,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
    'Thenuille' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 25
    },
    'Mythic Forest' : {
        'atk_bonus' : 0,
        'crit_bonus' : 2,
        'hp_bonus' : 0
    },
    'Lunaris' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 50
    },
    'Crumidia' : {
        'atk_bonus' : 10,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
    'Maritimiala' : {
        'atk_bonus' : 0,
        'crit_bonus' : 4,
        'hp_bonus' : 0
    },
    'Glakelys' : {
        'atk_bonus' : 5,
        'crit_bonus' : 0,
        'hp_bonus' : 25
    },
    None : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    }
}

RARITIES = {
    'Common' : {
        'low_atk' : 10,
        'high_atk' : 30,
        'low_crit' : 0,
        'high_crit' : 5
    },
    'Uncommon' : {
        'low_atk' : 30,
        'high_atk' : 60,
        'low_crit' : 0,
        'high_crit' : 5
    },
    'Rare' : {
        'low_atk' : 45,
        'high_atk' : 90,
        'low_crit' : 0,
        'high_crit' : 10
    },
    'Epic' : {
        'low_atk' : 75,
        'high_atk' : 120,
        'low_crit' : 0,
        'high_crit' : 15
    },
    'Legendary' : {
        'low_atk' : 100,
        'high_atk' : 150,
        'low_crit' : 5,
        'high_crit' : 20
    }
}

WEAPON_TYPES = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 
                'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 
                'Mace']