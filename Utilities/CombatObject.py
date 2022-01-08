import discord

import random

from Utilities import PlayerObject, Vars
from Utilities.AcolyteObject import Acolyte
from Utilities.AssociationObject import Association
from Utilities.ItemObject import Weapon, Armor


class Belligerent:
    """A class containing all combat-relevant information for a participant
    in some combat-oriented aspect of Ayesha.

    Essentially just the PlayerObject.Player butchered into a different role.
    However allows for the creation of pseudo-"empty objects" in the form of
    bosses, which the Player does not allow.

    Attributes
    ----------
    """
    def __init__(self, name : str, occ_type : str, attack : int, crit : int,
            hp : int, defense : int, disc_id : int = None, 
            weapon : Weapon = Weapon(), helmet : Armor = Armor(),
            bodypiece : Armor = Armor(), boots : Armor = Armor(),
            acolyte1 : Acolyte = Acolyte(), acolyte2 : Acolyte = Acolyte(),
            assc : Association = Association()):
        """
        Parameters
        ----------
        name : str
            The name of the player or boss
        occ_type : str
            The player's occupation if applicable. 'Boss' if boss.
        attack : int
            The attack stat
        crit : int
            The crit chance stat
        hp : int
            The maximum/starting HP value
        defense : int
            The defense stat
        disc_id : Optional[int]
            If occ_type is not 'Boss', pass the person's Discord ID
        weapon : Optional[ItemObject.Weapon]
            The weapon object that the person has equipped
        helmet : Optional[ItemObject.Armor]
            The armor object that the person has equipped in Helmet slot
        bodypiece : Optional[ItemObject.Armor]
            The armor object that the person has equipped in Bodypiece slot
        boots : Optional[ItemObject.Armor]
            The armor object that the person has equipped in Boots slot
        acolyte1 : Optional[AcolyteObject.Acolyte]
            The acolyte object that the person has equipped in slot 1
        acolyte2 : Optional[AcolyteObject.Acolyte]
            The acolyte object that the person has equipped in slot 2
        assc : Optional[AssociationObject.Association]
            The association that the person is in
        """
        # Useful information
        self.name = name
        self.type = occ_type
        self.disc_id = disc_id
        # Combat Stats
        self.attack = attack
        self.crit = crit
        self.max_hp = hp
        self.current_hp = hp
        self.defense = defense
        # Related objects
        self.weapon = weapon
        self.helmet = helmet
        self.bodypiece = bodypiece
        self.boots = boots
        self.acolyte1 = acolyte1
        self.acolyte2 = acolyte2
        self.assc = assc
        # For gameplay
        self.last_move = None
        self.damage = 0
        self.heal = 0

    @classmethod
    def load_player(cls, player : PlayerObject.Player):
        """Create a belligerent object of the 'Player' type as opposed to 'Boss'

        Parameters
        ----------
        player : PlayerObject.Player
            The player object for which this belligerent is being created
        """
        # General info
        name = player.char_name
        disc_id = player.disc_id
        occ = player.occupation
        # Combat Stats
        attack = player.get_attack()
        crit = player.get_crit()
        hp = player.get_hp()
        defense = player.get_defense()
        # Related objects
        weapon = player.equipped_item
        helmet = player.helmet
        bodypiece = player.bodypiece
        boots = player.boots
        acolyte1 = player.acolyte1
        acolyte2 = player.acolyte2
        assc = player.assc

        return cls(
            name, occ, attack, crit, hp, defense, disc_id, weapon, helmet,
            bodypiece, boots, acolyte1, acolyte2, assc)

    @classmethod
    def load_boss(cls, difficulty : int):
        """Create a belligerent object of the 'Boss' type """
        name = Vars.BOSSES[difficulty]
        attack = difficulty * 15
        crit = difficulty + 5
        hp = difficulty * 50
        defense = difficulty

        return cls(name, "Boss", attack, crit, hp, defense)


class ActionChoice(discord.ui.View):
    """"""
    def __init__(self, author_id : int):
        self.author_id = author_id
        self.choice = None
        super().__init__(timeout=10)

    @discord.ui.button(style=discord.ButtonStyle.blurple, 
            emoji="🗡️")
    async def attack(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Attack"
        button.disabled = True
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.grey, 
            emoji="\N{SHIELD}")
    async def block(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Block"
        button.disabled = True
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.green, 
            emoji="\N{CROSSED SWORDS}")
    async def parry(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Parry"
        button.disabled = True
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.red, 
            emoji="\u2764")
    async def heal(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Heal"
        button.disabled = True
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.grey, 
            emoji="\u23F1")
    async def bide(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Bide"
        button.disabled = True
        self.stop()

    async def interaction_check(self, 
            interaction : discord.Interaction) -> bool:
        return interaction.user.id == self.author_id


class InvalidMove(Exception):
    pass

# Passive the attacking players choice, followed by the defending players 
# choice. This will return a float that will be multiplied to the 
# damage they deal
ACTION_COMBOS = {
    "Attack" : {
        "Attack" : 1,
        "Block" : .05,
        "Parry" : .5,
        "Heal" : 1,
        "Bide" : .8
    },
    "Block" : {
        "Attack" : .25, # Note the inverse, Attack->Block does only .05
        "Block" : 0, # Punish mutual blocking
        "Parry" : .05,
        "Heal" : 0,
        "Bide" : 0
    },
    "Parry" : {
        "Attack" : .5,
        "Block" : 0,
        "Parry" : .75,
        "Heal" : .75,
        "Bide" : .5
    },
    "Heal" : {
        "Attack" : 0,
        "Block" : 0,
        "Parry" : 0,
        "Heal" : 0,
        "Bide" : 0
    },
    "Bide" : {
        "Attack" : 0,
        "Block" : 0,
        "Parry" : 0,
        "Heal" : 0,
        "Bide" : 0
    }
}

class CombatInstance:
    def __init__(self, player1 : Belligerent, player2 : Belligerent, 
            turn : int):
        self.turn = turn
        self.player1 = player1
        self.player2 = player2
        # Make sure both belligerents have active moves
        moves = ("Attack", "Block", "Parry", "Heal", "Bide")
        if self.player1.last_move not in moves:
            raise InvalidMove
        if self.player2.last_move not in moves:
            raise InvalidMove

        # Create a raw damage count
        self.player1.damage = random.randint(
            self.player1.attack, self.player1.attack + 20)
        self.player2.damage = random.randint(
            self.player2.attack, self.player2.attack + 20)

        # Determine critical strikes
        p1_crit_cond = player1.last_move in ("Attack", "Block", "Parry")
        p2_crit_cond = player2.last_move in ("Attack", "Block", "Parry")
        if p1_crit_cond and random.randint(1, 100) < self.player1.crit:
            self.player1 = self.on_critical_hit(self.player1)
        if p2_crit_cond and random.randint(1, 100) < self.player2.crit:
            self.player2 = self.on_critical_hit(self.player2)

        # Calculate damage multipliers based off action combinations
        self.player1.damage *= ACTION_COMBOS[self.player1.last_move]\
            [self.player2.last_move]
        self.player2.damage *= ACTION_COMBOS[self.player2.last_move]\
            [self.player1.last_move]

        # Unique interactions with attack choices
        self.player1, self.player2 = self.run_events(
            agent=self.player1, object=self.player2)
        self.player2, self.player1 = self.run_events(
            agent=self.player2, object=self.player1)

        # Cast everything to int
        self.player1.attack = int(self.player1.attack)
        self.player1.crit = int(self.player1.crit)
        self.player1.current_hp = int(self.player1.current_hp)
        self.player1.defense = int(self.player1.defense)
        self.player1.damage = int(self.player1.damage)
        self.player1.heal = int(self.player1.heal)

        self.player2.attack = int(self.player2.attack)
        self.player2.crit = int(self.player2.crit)
        self.player2.current_hp = int(self.player2.current_hp)
        self.player2.defense = int(self.player2.defense)
        self.player2.damage = int(self.player2.damage)
        self.player2.heal = int(self.player2.heal)

    def apply_damage(self):
        """Actually edits the players' stats and returns their objects to
        the gameloop. Essentially the de-initializer.
        Returns 2 'Belligerent' objects.
        """
        self.player1.current_hp += self.player1.heal - self.player2.damage
        self.player2.current_hp += self.player2.heal - self.player1.damage

        # Reset everything to 0
        self.player1.last_move = None
        self.player1.damage = 0
        self.player1.heal = 0
        self.player2.last_move = None
        self.player2.damage = 0
        self.player2.heal = 0

        return self.player1, self.player2

    def get_turn_str(self):
        """Returns a string detailing what happened in combat."""
        output = f"**Turn {self.turn}:** "
        for p in (self.player1, self.player2):
            if p.last_move in ("Attack", "Block", "Parry"):
                output += (
                    f"**{p.name}** decided to {p.last_move.lower()}, "
                    f"and dealt **{p.damage}** damage. ")
            elif p.last_move == "Heal":
                output += f"**{p.name}** healed themselves for `{p.heal}` HP. "
            else:
                output += (
                    f"**{p.name}** saved their strength for a turn and "
                    f"received a 10% ATK boost! ")
        return output

    # Independent event as it happens during damage calculation
    def on_critical_hit(self, player : Belligerent):
        # Base damage boost from critical strikes
        bonus_occ = player.type == "Engineer"
        player.damage *= 1.75 if bonus_occ else 1.5

        # Applicable acolytes: Aulus, Ayesha
        acolytes = [a.acolyte_name for a in (player.acolyte1, player.acolyte2)]
        if "Aulus" in acolytes:
            player.attack += 50
        if "Ayesha" in acolytes:
            player.heal += player.attack / 5

        # Accessory Effects?
        # Boss Effects?

        return player

    # Below events will all be part of on_damage
    def run_events(self, agent : Belligerent, object : Belligerent):
        acolytes = [a.acolyte_name for a in (agent.acolyte1, agent.acolyte2)]
        # ON_DAMAGE : Any time the agent deals damage
        if "Paterius" in acolytes:
            agent.damage += 15

        # ON_ATTACK : Agent attacks


        # ON_BLOCK : Agent blocks


        # ON_PARRY : Agent parries


        # ON_HEAL : Agent heals
        if agent.last_move == "Heal":
            agent.heal += agent.max_hp / 10
            agent.heal *= 2 if agent.type == "Butcher" else 1

        # ON_BIDE : Agents bides
        if agent.last_move == "Bide":
            agent.attack *= 1.1

        # GENERAL DAMAGE CALC
        if agent.type == "Boss" and object.type == "Leatherworker":
            # Leatherworkers get more defense in PvE
            agent.damage *= 0.85

        return agent, object

    def on_combat_begin(self):
        return

    def on_combat_end(self):
        return

    @staticmethod
    def on_turn_end(player1 : Belligerent, player2 : Belligerent):
        return player1, player2






# Outlined below is a general idea of how PvE was performed before
"""
Loads Player Battle Info
	Discord ID
	Attack, Crit, HP (current), Max_HP
	Player's Class
	Acolyte 1 and 2 (can become AcolyteObject)
	Strategy
Loads Enemy Battle Info

Creates combat embed
	Displays combat stats and action messages

Battle begins with turn counter initialized at 0
(Event) on game begin
Chooses random player and enemy actions
Calculates damage and heal amounts
	(Event) acolytes dealing damage
	Determines critical strike
		(Event) Engineer class bonus
		(Event) acolytes on crit
		(Event) boss on crit
(Event) acolytes on turn end
(Event) boss on turn end
Butcher and Leatherworker applied to damage and HP
FINALLY actually changes participants stats accordingly
Checks for victory/loss

Also includes a strategy command (maybe unnecessary)
"""