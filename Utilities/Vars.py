ACOLYTE_LIST_PATH = r'F:\OneDrive\Python_Projects\Ayesha_Rewrite\Assets\Acolyte_List.json'

ABLUE =  0xBEDCF6

ACCESSORY_BONUS = {
    'Lucky' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Thorned' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Strong' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Consistent' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Shiny' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Flexible' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Thick' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Old' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Regal' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    },
    'Demonic' : {
        'Wood' : None,
        'Glass' : None,
        'Copper' : None,
        'Jade' : None,
        'Pearl' : None,
        'Aquamarine' : None,
        'Sapphire' : None,
        'Amethyst' : None,
        'Ruby' : None,
        'Garnet' : None,
        'Diamond' : None,
        'Emerald' : None,
        'Black Opal' : None
    }
}

ARMOR_DEFENSE = {
    'Helmet' : {
        'Cloth' : 1,
        'Wood' : 2,
        'Silk' : 3,
        'Leather' : 5,
        'Gambeson' : 6,
        'Wolfskin' : 7,
        'Bearskin' : 8,
        'Bronze' : 7,
        'Ceramic Plate' : 10,
        'Chainmail' : 11,
        'Iron' : 12,
        'Steel' : 15,
        'Mysterious' : 16,
        'Dragonscale' : 17
    },
    'Bodypiece' : {
        'Cloth' : 3,
        'Wood' : 5,
        'Silk' : 7,
        'Leather' : 8,
        'Gambeson' : 10,
        'Wolfskin' : 12,
        'Bearskin' : 13,
        'Bronze' : 12,
        'Ceramic Plate' : 14,
        'Chainmail' : 15,
        'Iron' : 16,
        'Steel' : 18,
        'Mysterious' : 20,
        'Dragonscale' : 22
    },
    'Boots' : {
        'Cloth' : 1,
        'Wood' : 1,
        'Silk' : 1,
        'Leather' : 3,
        'Gambeson' : 5,
        'Wolfskin' : 5,
        'Bearskin' : 5,
        'Bronze' : 7,
        'Ceramic Plate' : 1,
        'Chainmail' : 8,
        'Iron' : 10,
        'Steel' : 12,
        'Mysterious' : 15,
        'Dragonscale' : 18
    },
}

MATERIALS = ["Fur", "Bone", "Iron", "Silver", "Wood", "Wheat", "Oat", "Reeds",
             "Pine", "Moss", "Cacao"]

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
    'Aramithea' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
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
    'Sunset' : {
        'atk_bonus' : 0,
        'crit_bonus' : 0,
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
        'high_crit' : 5,
        'low_gold' : 1,
        'high_gold' : 20
    },
    'Uncommon' : {
        'low_atk' : 30,
        'high_atk' : 60,
        'low_crit' : 0,
        'high_crit' : 5,
        'low_gold' : 15,
        'high_gold' : 30
    },
    'Rare' : {
        'low_atk' : 45,
        'high_atk' : 90,
        'low_crit' : 0,
        'high_crit' : 10,
        'low_gold' : 75,
        'high_gold' : 150
    },
    'Epic' : {
        'low_atk' : 75,
        'high_atk' : 120,
        'low_crit' : 0,
        'high_crit' : 15,
        'low_gold' : 400,
        'high_gold' : 700
    },
    'Legendary' : {
        'low_atk' : 100,
        'high_atk' : 150,
        'low_crit' : 5,
        'high_crit' : 20,
        'low_gold' : 2000,
        'high_gold' : 3000
    }
}

# These are valid map locations. When using with travel, pass the player's
# current location, then Destinations[destination], to get adventure length
TRAVEL_LOCATIONS = {
    'Aramithea' : {
        'Biome' : 'City', 
        'Drops' : 'You can `upgrade` your weapons here.',
        'Destinations' : {
            'Aramithea' : 0,
            'Mythic Forest' : 1800,
            'Thenuille' : 1800,
            'Fernheim' : 1800,
            'Sunset Prairie' : 1800,
            'Riverburn' : 1800,
            'Thanderlans' : 3600,
            'Glakelys' : 3600,
            'Russe' : 7200,
            'Croire' : 7200,
            'Crumidia' : 10800,
            'Kucre' : 10800
        }
    },
    'Mythic Forest' : {
        'Biome' : 'Forest',
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `wood`.',
        'Destinations' : {
            'Aramithea' : 1800,
            'Mythic Forest' : 0,
            'Thenuille' : 1800,
            'Fernheim' : 3600,
            'Sunset Prairie' : 1800,
            'Riverburn' : 3600,
            'Thanderlans' : 7200,
            'Glakelys' : 7200,
            'Russe' : 10800,
            'Croire' : 10800,
            'Crumidia' : 10800,
            'Kucre' : 7200
        }
    }, 
    'Thenuille' : {
        'Biome' : 'Town', 
        'Drops' : 'You can `upgrade` your weapons here and `fish`.',
        'Destinations' : {
            'Aramithea' : 1800,
            'Mythic Forest' : 1800,
            'Thenuille' : 0,
            'Fernheim' : 1800,
            'Sunset Prairie' : 1800,
            'Riverburn' : 1800,
            'Thanderlans' : 3600,
            'Glakelys' : 3600,
            'Russe' : 10800,
            'Croire' : 7200,
            'Crumidia' : 10800,
            'Kucre' : 10800
        }
    },
    'Fernheim' : {
        'Biome' : 'Grassland', 
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `wheat`.',
        'Destinations' : {
            'Aramithea' : 1800,
            'Mythic Forest' : 3600,
            'Thenuille' : 1800,
            'Fernheim' : 0,
            'Sunset Prairie' : 1800,
            'Riverburn' : 1800,
            'Thanderlans' : 3600,
            'Glakelys' : 3600,
            'Russe' : 10800,
            'Croire' : 7200,
            'Crumidia' : 10800,
            'Kucre' : 14400
        }
    },
    'Sunset Prairie' : {
        'Biome' : 'Grassland', 
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `oats`.',
        'Destinations' : {
            'Aramithea' : 0,
            'Mythic Forest' : 0,
            'Thenuille' : 0,
            'Fernheim' : 0,
            'Sunset Prairie' : 0,
            'Riverburn' : 0,
            'Thanderlans' : 0,
            'Glakelys' : 0,
            'Russe' : 0,
            'Croire' : 0,
            'Crumidia' : 0,
            'Kucre' : 14400
        }
    },
    'Riverburn' : {
        'Biome' : 'City', 
        'Drops' : 'You can `upgrade` your weapons here.',
        'Destinations' : {
            'Aramithea' : 1800,
            'Mythic Forest' : 3600,
            'Thenuille' : 1800,
            'Fernheim' : 1800,
            'Sunset Prairie' : 3600,
            'Riverburn' : 0,
            'Thanderlans' : 3600,
            'Glakelys' : 1800,
            'Russe' : 9000,
            'Croire' : 7200,
            'Crumidia' : 9000,
            'Kucre' : 14400
        }
    },
    'Thanderlans' : {
        'Biome' : 'Marsh', 
        'Drops' : 'You can `forage` here for `reeds`.',
        'Destinations' : {
            'Aramithea' : 3600,
            'Mythic Forest' : 7200,
            'Thenuille' : 3600,
            'Fernheim' : 3600,
            'Sunset Prairie' : 9000,
            'Riverburn' : 3600,
            'Thanderlans' : 0,
            'Glakelys' : 1800,
            'Russe' : 3600,
            'Croire' : 1800,
            'Crumidia' : 7200,
            'Kucre' : 10800
        }
    },
    'Glakelys' : {
        'Biome' : 'Grassland', 
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `oats`.',
        'Destinations' : {
            'Aramithea' : 3600,
            'Mythic Forest' : 7200,
            'Thenuille' : 3600,
            'Fernheim' : 3600,
            'Sunset Prairie' : 7200,
            'Riverburn' : 1800,
            'Thanderlans' : 1800,
            'Glakelys' : 0,
            'Russe' : 7200,
            'Croire' : 7200,
            'Crumidia' : 7200,
            'Kucre' : 10800
        }
    },
    'Russe' : {
        'Biome' : 'Taiga', 
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, `pine`, and `moss`.',
        'Destinations' : {
            'Aramithea' : 7200,
            'Mythic Forest' : 10800,
            'Thenuille' : 7200,
            'Fernheim' : 7200,
            'Sunset Prairie' : 10800,
            'Riverburn' : 7200,
            'Thanderlans' : 3600,
            'Glakelys' : 5400,
            'Russe' : 0,
            'Croire' : 1800,
            'Crumidia' : 3600,
            'Kucre' : 14400
        }
    },
    'Croire' : {
        'Biome' : 'Grassland', 
        'Drops' : 'You can `hunt` and `forage` here for `fur`, and `wheat`.',
        'Destinations' : {
            'Aramithea' : 7200,
            'Mythic Forest' : 10800,
            'Thenuille' : 7200,
            'Fernheim' : 7200,
            'Sunset Prairie' : 10800,
            'Riverburn' : 7200,
            'Thanderlans' : 1800,
            'Glakelys' : 3600,
            'Russe' : 3600,
            'Croire' : 0,
            'Crumidia' : 1800,
            'Kucre' : 14400
        }
    },
    'Crumidia' : {
        'Biome' : 'Hills', 
        'Drops' : 'You can `mine` and `forage` here for `iron` and `silver`.',
        'Destinations' : {
            'Aramithea' : 5400,
            'Mythic Forest' : 7200,
            'Thenuille' : 3600,
            'Fernheim' : 5400,
            'Sunset Prairie' : 10800,
            'Riverburn' : 7200,
            'Thanderlans' : 3600,
            'Glakelys' : 5400,
            'Russe' : 7200,
            'Croire' : 1800,
            'Crumidia' : 0,
            'Kucre' : 7200
        }
    },
    'Kucre' : {
        'Biome' : 'Jungle', 
        'Drops' : 'You can `forage` here for `cacao`.',
        'Destinations' : {
            'Aramithea' : 14400,
            'Mythic Forest' : 10800,
            'Thenuille' : 7200,
            'Fernheim' : 10800,
            'Sunset Prairie' : 14400,
            'Riverburn' : 10800,
            'Thanderlans' : 7200,
            'Glakelys' : 7200,
            'Russe' : 10800,
            'Croire' : 7200,
            'Crumidia' : 7200,
            'Kucre' : 0
        }
    }
}

WEAPON_TYPES = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 
                'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 
                'Mace']