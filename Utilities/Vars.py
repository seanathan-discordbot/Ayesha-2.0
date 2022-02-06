# ACOLYTE_LIST_PATH = r'F:\OneDrive\Python_Projects\Ayesha_Rewrite\Assets\Acolyte_List.json'
ACOLYTE_LIST_PATH = r'C:\Users\sebas\OneDrive\Python_Projects\Ayesha_Rewrite\Assets\Acolyte_List.json'

ABLUE = 0xBEDCF6

ACCESSORY_BONUS = {
    'Lucky' : { # x% bonus to gold and xp in PvE, Travel, and Expeditions
        'Wood' : 1,
        'Glass' : 2,
        'Copper' : 3,
        'Jade' : 4,
        'Pearl' : 5,
        'Aquamarine' : 6,
        'Sapphire' : 7,
        'Amethyst' : 8,
        'Ruby' : 10,
        'Garnet' : 11,
        'Diamond' : 12,
        'Emerald' : 16,
        'Black Opal' : 20
    },
    'Thorned' : { # x% damage reflected when hit in PvE and PvP
        'Wood' : 1,
        'Glass' : 2,
        'Copper' : 3,
        'Jade' : 3,
        'Pearl' : 4,
        'Aquamarine' : 4,
        'Sapphire' : 5,
        'Amethyst' : 5,
        'Ruby' : 5,
        'Garnet' : 6,
        'Diamond' : 6,
        'Emerald' : 8,
        'Black Opal' : 10
    },
    'Strong' : { # additional DEF
        'Wood' : 3,
        'Glass' : 3,
        'Copper' : 4,
        'Jade' : 4,
        'Pearl' : 5,
        'Aquamarine' : 5,
        'Sapphire' : 6,
        'Amethyst' : 6,
        'Ruby' : 6,
        'Garnet' : 7,
        'Diamond' : 8,
        'Emerald' : 9,
        'Black Opal' : 10
    },
    'Shiny' : { # reduces critdmg by x%
        'Wood' : 5,
        'Glass' : 8,
        'Copper' : 10,
        'Jade' : 12,
        'Pearl' : 13,
        'Aquamarine' : 15,
        'Sapphire' : 16,
        'Amethyst' : 18,
        'Ruby' : 20,
        'Garnet' : 23,
        'Diamond' : 25,
        'Emerald' : 30,
        'Black Opal' : 33
    },
    'Flexible' : { # increase crit rate by x%
        'Wood' : 2,
        'Glass' : 2,
        'Copper' : 2,
        'Jade' : 3,
        'Pearl' : 3,
        'Aquamarine' : 4,
        'Sapphire' : 4,
        'Amethyst' : 4,
        'Ruby' : 5,
        'Garnet' : 5,
        'Diamond' : 6,
        'Emerald' : 8,
        'Black Opal' : 10
    },
    'Thick' : { # increases your HP by x
        'Wood' : 70,
        'Glass' : 80,
        'Copper' : 90,
        'Jade' : 100,
        'Pearl' : 125,
        'Aquamarine' : 150,
        'Sapphire' : 175,
        'Amethyst' : 200,
        'Ruby' : 225,
        'Garnet' : 250,
        'Diamond' : 300,
        'Emerald' : 350,
        'Black Opal' : 400
    },
    'Old' : { # Gain gravitas when defeating a boss above level 25 in PvE
        'Wood' : 1,
        'Glass' : 1,
        'Copper' : 1,
        'Jade' : 2,
        'Pearl' : 2,
        'Aquamarine' : 2,
        'Sapphire' : 3,
        'Amethyst' : 3,
        'Ruby' : 3,
        'Garnet' : 4,
        'Diamond' : 5,
        'Emerald' : 6,
        'Black Opal' : 7
    },
    'Regal' : { # Pay x% less taxes 
        'Wood' : 5,
        'Glass' : 5,
        'Copper' : 7,
        'Jade' : 8,
        'Pearl' : 10,
        'Aquamarine' : 12,
        'Sapphire' : 13,
        'Amethyst' : 15,
        'Ruby' : 16,
        'Garnet' : 18,
        'Diamond' : 20,
        'Emerald' : 23,
        'Black Opal' : 27
    },
    'Demonic' : { # ATK increase
        'Wood' : 25,
        'Glass' : 27,
        'Copper' : 30,
        'Jade' : 31,
        'Pearl' : 32,
        'Aquamarine' : 34,
        'Sapphire' : 35,
        'Amethyst' : 38,
        'Ruby' : 40,
        'Garnet' : 42,
        'Diamond' : 45,
        'Emerald' : 50,
        'Black Opal' : 60
    }
}

ACCESSORY_SALE_PRICES = {
    material : {
        'low' : 30 * i**2,
        'high' : 50 * i**2
    }
    for i, material in enumerate(ACCESSORY_BONUS["Lucky"], start=1)
}

ARMOR_DEFENSE = {
    'Helmet' : {
        'Cloth' : 1,
        'Wood' : 2,
        'Silk' : 3,
        'Leather' : 3,
        'Gambeson' : 3,
        'Wolfskin' : 4,
        'Bearskin' : 4,
        'Bronze' : 5,
        'Ceramic Plate' : 6,
        'Chainmail' : 6,
        'Iron' : 7,
        'Steel' : 9,
        'Mysterious' : 11,
        'Dragonscale' : 12
    },
    'Bodypiece' : {
        'Cloth' : 3,
        'Wood' : 5,
        'Silk' : 6,
        'Leather' : 7,
        'Gambeson' : 7,
        'Wolfskin' : 8,
        'Bearskin' : 9,
        'Bronze' : 9,
        'Ceramic Plate' : 10,
        'Chainmail' : 10,
        'Iron' : 11,
        'Steel' : 13,
        'Mysterious' : 15,
        'Dragonscale' : 16
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
        'Iron' : 9,
        'Steel' : 10,
        'Mysterious' : 12,
        'Dragonscale' : 13
    },
}

ARMOR_SALE_PRICES = {
    material : {
        'low' : 15 * i**2,
        'high' : 25 * i**2
    }
    for i, material in enumerate(ARMOR_DEFENSE["Helmet"], start=1)
}

ANNOUNCEMENT_CHANNEL = 854493268581679104
RAIDER_ROLE = 854737863253557288

BOSSES = {
    1 : "Bortoise",
    2 : "Tavern Drunkard",
    3 : "Thief",
    4 : "Wild Boar",
    5 : "Sean",
    6 : "Roadside Brigands",
    7 : "Verricosus",
    8 : "Corrupt Knight",
    9 : "Rabid Bear",
    10 : "Maritimialan Shaman",
    11 : "Apprecenticeship Loan Debt Collector",
    12 : "Maritimialana Blood Oathsworn",
    13 : "Moonlight Wolf Pack",
    14 : "Cursed Huntress",
    15 : "Crumidian Warriors",
    16 : "Naysayers of the Larry Almighty",
    17 : "John",
    18 : "Osprey Imperial Assassin",
    19 : "Arquitenio",
    20 : "Tomyris",
    21 : "Lucius Porcius Magnus Dux",
    22 : "Laidirix",
    23 : "Sanguirix",
    24 : "Supreme Ducc",
    25 : "Draconicus Rex"
}

DEFAULT_ICON = "https://upload.wikimedia.org/wikipedia/commons/a/ac/White_flag_of_surrender.svg"

MATERIALS = ["Fur", "Bone", "Iron", "Silver", "Wood", "Wheat", "Oat", "Reeds",
             "Pine", "Moss", "Cacao"]

OCCUPATIONS = {
    'Soldier' : {
        'Name' : 'Soldier',
        'Desc' : 'You are a retainer of your local lord, trained in the discipline of swordsmanship.',
        'Passive' : '10% bonus to character ATK; +1 gravitas/day',
        'Command' : 'Deal 50% more damage when doing `raid attack`',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Spear", "Sword")
    },
    'Blacksmith' : {
        'Name' : 'Blacksmith',
        'Desc' : 'You\'ve spent years as the apprentice of a hardy blacksmith, and now a master in the art of forging.',
        'Passive' : 'Gain double gold and resources from mining (`/work`), and pay half cost from `/upgrade`.',
        'Command' : '`/merge` will increase weapon ATK by 2 instead of 1.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Greatsword", "Gauntlets")
    },
    'Farmer' : {
        'Name' : 'Farmer',
        'Desc' : 'You are a lowly farmer, but farming is no easy job.',
        'Passive' : '+4 gravitas/day',
        'Command' : 'Gain 20% extra gravitas on urban expeditions; lose 50% less gravitas on wilderness expeditions.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Sling", "Falx")
    },
    'Hunter' : {
        'Name' : 'Hunter',
        'Desc' : 'The wild is your domain; no game is unconquerable.',
        'Passive' : 'Gain double gold and resources from `hunt`.',
        'Command' : 'Gain a first turn damage bonus on PvE/PvP',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Bow", "Javelin")
    },
    'Merchant' : {
        'Name' : 'Merchant',
        'Desc' : 'Screw you, exploiter of others\' labor.',
        'Passive' : 'Gain 50% increased gold from the `/sell` command.',
        'Command' : 'Guaranteed weapon upon defeating a boss in PvE.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Dagger", "Mace")
    },
    'Traveler' : {
        'Name' : 'Traveler',
        'Desc' : 'The wild forests north await, as do the raging seas to the south. What will you discover?',
        'Passive' : 'Gain triple gold from the `/travel` command and double materials from foraging (`/work`) command.',
        'Command' : '50% chance to gain an acolyte from expeditions lasting longer than 72 hours. 75% chance if over 144 hours.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Staff", "Javelin")
    },
    'Leatherworker' : {
        'Name' : 'Leatherworker',
        'Desc' : 'The finest protective gear, saddles, and equipment have your name on it.',
        'Passive' : 'Increases DEF by 3% on each piece of equipped armor.',
        'Command' : 'Take 15% less damage from every hit in PvE battles.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Mace", "Axe")
    },
    'Butcher' : {
        'Name' : 'Butcher',
        'Desc' : 'Meat. What would one do without it?',
        'Passive' : 'Gain 250 HP.',
        'Command' : '100% heal bonus in PvE.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 250,
        'weapon_bonus' : ("Axe", "Dagger")
    },
    'Engineer' : {
        'Name' : 'Engineer',
        'Desc' : 'Your lord praises the seemingly impossible design of his new manor.',
        'Passive' : 'Gain increased rewards from the special commands of whatever association you are in: `bh steal`, `guild invest`, or `cl usurp`.',
        'Command' : 'Critical hits in PvE and PvP deal 1.75x damage instead of 1.5x',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Trebuchet", "Falx")
    },
    'Scribe' : {
        'Name' : 'Scribe',
        'Desc' : 'Despite the might of your lord, you have learned quite a bit about everything, too.',
        'Passive' : '+10 Crit; +1 gravitas daily',
        'Command' : '15% reduced tax rate.',
        'atk_bonus' : 0,
        'crit_bonus' : 10,
        'hp_bonus' : 0,
        'weapon_bonus' : ("Sword", "Dagger")
    },
    None : {
        'Name' : None,
        'Desc' : None,
        'Passive' : None,
        'Command' : None,
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0,
        'weapon_bonus' : []
    }
}

ORIGINS = {
    'Aramithea' : {
        'Name' : 'Aramithea',
        'Desc' : 'You\'re a metropolitan. Aramithea, the largest city on Rabidus, must have at least a million people, and a niche for everybody.',
        'Passive' : '+5 gravitas/day',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
    'Riverburn' : {
        'Name' : 'Riverburn',
        'Desc' : 'The great rival of Aramithea; Will you bring your city to become the center of the kingdom?',
        'Passive' : '+5 ATK, +3 gravitas/day',
        'atk_bonus' : 5,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
    'Thenuille' : {
        'Name' : 'Thenuille',
        'Desc' : 'You love the sea; you love exploration; you love trade. From here one can go anywhere, and be anything.',
        'Passive' : '+25 HP, +3 gravitas/day',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 25
    },
    'Mythic Forest' : {
        'Name' : 'Mythic Forest',
        'Desc' : 'You come from the lands down south, covered in forest. You could probably hit a deer square between the eyes blindfolded.',
        'Passive' : '+2 Crit, +1 gravitas/day',
        'atk_bonus' : 0,
        'crit_bonus' : 2,
        'hp_bonus' : 0
    },
    'Sunset' : {
        'Name' : 'Sunset',
        'Desc' : 'Nothing is more peaceful than an autumn afternoon in the prairie.',
        'Passive' : 'Pay 5% less in taxes.',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
    'Lunaris' : {
        'Name' : 'Lunaris',
        'Desc' : 'The crossroads of civilization; the battleground of those from the north, west, and east. Your times here have hardened you.',
        'Passive' : '+50 HP, +1 gravitas/day',
        'atk_bonus' : 0,
        'crit_bonus' : 0,
        'hp_bonus' : 50
    },
    'Crumidia' : {
        'Name' : 'Crumidia',
        'Desc' : 'The foothills have turned you into a strong warrior. Perhaps you will seek domination over your adversaries?',
        'Passive' : '+10 ATK, +1 gravitas/day',
        'atk_bonus' : 10,
        'crit_bonus' : 0,
        'hp_bonus' : 0
    },
    'Maritimiala' : {
        'Name' : 'Maritimiala',
        'Desc' : 'North of the mountains, the Maritimialan tribes look lustfully upon the fertile plains below. Will you seek integration, or domination?',
        'Passive' : '+4 Crit',
        'atk_bonus' : 0,
        'crit_bonus' : 4,
        'hp_bonus' : 0
    },
    'Glakelys' : {
        'Name' : 'Glakelys',
        'Desc' : 'The small towns beyond Riverburn disregard the Aramithean elite. The first line of defense from invasions from Lunaris, the Glakelys are as tribal as they were 300 years ago.',
        'Passive' : '+5 ATK, +25 HP',
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
        'Forage' : None,
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
        'Forage' : 'Wood',
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
        'Forage' : None,
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
        'Forage' : 'Wheat',
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
        'Forage' : 'Oat',
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
        'Forage' : None,
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
        'Forage' : 'Reeds',
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
        'Forage' : 'Oat',
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
        'Forage' : 'Pine, Moss',
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
        'Forage' : 'Wheat',
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
        'Forage' : 'Iron, Silver',
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
        'Forage' : 'Cacao',
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
TERRITORIES = [t for t in TRAVEL_LOCATIONS 
    if TRAVEL_LOCATIONS[t]["Biome"] not in ("City", "Town")]

WEAPON_TYPES = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 
                'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 
                'Mace']