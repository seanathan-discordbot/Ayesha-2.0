import discord

import random
from typing import Optional

from Utilities import PlayerObject, Vars
from Utilities.AcolyteObject import EmptyAcolyte, InfoAcolyte, OwnedAcolyte
from Utilities.AssociationObject import Association
from Utilities.ItemObject import Accessory, Weapon, Armor


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
            accessory : Accessory = Accessory(),
            acolyte1 : EmptyAcolyte = EmptyAcolyte(), 
            acolyte2 : EmptyAcolyte = EmptyAcolyte(),
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
        accessory : Optional[ItemObject.Accessory]
            The accessory object that the person has equipped
        acolyte1 : Optional[EmptyAcolyte]
            The acolyte object that the person has equipped in slot 1
        acolyte2 : Optional[EmptyAcolyte]
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
        self.accessory = accessory
        self.acolyte1 = acolyte1
        self.acolyte2 = acolyte2
        self.assc = assc
        # For gameplay
        self.last_move = None
        self.crit_hit = False
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
        crit = player.get_crit_rate()
        hp = player.get_hp()
        defense = player.get_defense()
        # Related objects
        weapon = player.equipped_item
        helmet = player.helmet
        bodypiece = player.bodypiece
        boots = player.boots
        accessory = player.accessory
        acolyte1 = player.acolyte1
        acolyte2 = player.acolyte2
        assc = player.assc

        # ON_PLAYER_LOAD event lol
        try:
            arsaces = player.get_acolyte("Arsaces")
            attack += crit * arsaces.get_effect_modifier(0)
            hp += crit * arsaces.get_effect_modifier(1)
            crit = 0
        except AttributeError:
            pass

        return cls(
            name, occ, attack, crit, hp, defense, disc_id, weapon, helmet,
            bodypiece, boots, accessory, acolyte1, acolyte2, assc)

    @classmethod
    def load_boss(cls, difficulty : int):
        """Create a belligerent object of the 'Boss' type """
        if difficulty <= 25:
            name = Vars.BOSSES[difficulty]
        else:
            names = ( # credit to rea
                "Spinning Sphinx", "Black Witch of the Prairie", "Crocc",
                "James Juvenile", "Shorttimber King", "Darkness of the Dark",
                "Sealed Demon Lord", "Elysia", "Three-headed Anaconda",
                "Blood Tiger", "The Great Imyutarian", "Corrupted Dragon Slayer"
            )
            name = random.choice(names)

        if difficulty == 1:
            attack = 1
            crit = 0
            hp = 50
            defense = 10
        elif difficulty < 16:
            attack = difficulty * 7
            crit = int(difficulty * 1.2) + 5
            hp = difficulty * 67
            defense = int(difficulty * 1.2)
        elif difficulty < 25:
            attack = difficulty * 10
            crit = int(difficulty * 1.5) + 5
            hp = difficulty * 75
            defense = int(difficulty * 1.3)
        elif difficulty < 40:
            attack = difficulty * 20
            crit = 65
            hp = difficulty * 125
            defense = 40
        elif difficulty < 50:
            attack = difficulty * 25
            crit = 75
            hp = difficulty * 140
            defense = 55
        else:
            attack = difficulty * 28
            crit = 78
            hp = difficulty * 150
            defense = 70

        return cls(name, "Boss", attack, crit, hp, defense)

    def get_acolyte(self, name : str) -> Optional[EmptyAcolyte]:
        """Returns the equipped acolyte with the name given. If no acolyte
        with the name is equipped, `None` is returned
        """
        if self.acolyte1.name == name:
            return self.acolyte1
        elif self.acolyte2.name == name:
            return self.acolyte2
        else:
            return None


class ActionChoice(discord.ui.View):
    """"""
    def __init__(self, author_id : int):
        self.author_id = author_id
        self.choice = None
        super().__init__(timeout=30)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🗡️")
    async def attack(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Attack"
        await interaction.response.edit_message(content=None)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\N{SHIELD}")
    async def block(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Block"
        await interaction.response.edit_message(content=None)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.green, emoji="\N{CROSSED SWORDS}")
    async def parry(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Parry"
        await interaction.response.edit_message(content=None)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="\u2764")
    async def heal(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Heal"
        await interaction.response.edit_message(content=None)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\u23F1")
    async def bide(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.choice = "Bide"
        await interaction.response.edit_message(content=None)
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
        "Block" : .25,
        "Parry" : .67,
        "Heal" : .67,
        "Bide" : .10
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
            self.player1, self.player2 = self.on_critical_hit(
                agent=self.player1, object=self.player2)
        if p2_crit_cond and random.randint(1, 100) < self.player2.crit:
            self.player2 , self.player1 = self.on_critical_hit(
                agent=self.player2, object=self.player1)

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

        # Reduce damage by opponent defense
        self.player1.damage *= (100 - self.player2.defense) / 100
        self.player2.damage *= (100 - self.player1.defense) / 100

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
        self.player1.crit_hit = False
        self.player2.last_move = None
        self.player2.damage = 0
        self.player2.heal = 0
        self.player2.crit_hit = False

        return self.player1, self.player2

    def get_turn_str(self):
        """Returns a string detailing what happened in combat."""
        output = f"**Turn {self.turn}:** "
        for p in (self.player1, self.player2):
            if p.last_move in ("Attack", "Block", "Parry"):
                temp = {
                    "Attack" : "🗡️",
                    "Block" : "\N{SHIELD}",
                    "Parry" : "\N{CROSSED SWORDS}"
                }
                if p.crit_hit:
                    output += (
                        f"**{p.name}** critically {temp[p.last_move]} for "
                        f"**{p.damage}** damage. ")
                else:
                    output += (
                        f"**{p.name}** {temp[p.last_move]} for **{p.damage}** "
                        f"damage. ")
            elif p.last_move == "Heal":
                output += f"**{p.name}** \u2764 for **{p.heal}** HP. "
            else:
                output += (
                    f"**{p.name}** decided to \u23F1. ")
        return output

    # Independent event as it happens during damage calculation
    def on_critical_hit(self, agent : Belligerent, object : Belligerent):
        # Base damage boost from critical strikes
        bonus_occ = agent.type == "Engineer"
        crit_bonus = .75 if bonus_occ else .5
        if agent.assc.type == "College":
            crit_bonus += .05 * agent.assc.get_level()
        agent.crit_hit = True

        # Applicable acolytes: Aulus, Ayesha
        try:
            aulus = agent.get_acolyte("Aulus")
            agent.attack += aulus.get_effect_modifier(0)
        except AttributeError:
            pass

        try:
            ayesha = agent.get_acolyte("Ayesha")
            agent.heal += agent.attack * .01 * ayesha.get_effect_modifier(0)
        except AttributeError:
            pass

        # Accessory Effects
        if object.accessory.prefix == "Shiny": # reduce crit dmg
            mult = Vars.ACCESSORY_BONUS["Shiny"][object.accessory.type] / 100.0
            crit_bonus *= 1 - mult

        # Boss Effects?

        # Apply crit bonuses
        agent.damage *= 1 + crit_bonus

        return agent, object

    # Below events will all be part of on_damage
    def run_events(self, agent : Belligerent, object : Belligerent):
        # ON_DAMAGE : Any time the agent deals damage
        try:
            paterius = agent.get_acolyte("Paterius")
            agent.damage = agent.damage * \
                (1 + paterius.get_effect_modifier(0) * .01) + 15
        except AttributeError:
            pass

        if self.turn == 1 and agent.type == "Hunter":
            # Hunters get first hit bonus
            agent.damage += agent.attack

        # ON_ATTACK : Agent attacks


        # ON_BLOCK : Agent blocks
        if object.last_move == "Attack":
            try:
                demi = agent.get_acolyte("Demi")
                agent.damage += agent.defense * demi.get_effect_modifier(0) * .01
            except AttributeError:
                pass


        # ON_PARRY : Agent parries


        # ON_HEAL : Agent heals
        if agent.last_move == "Heal":
            if agent.type != "Boss":
                agent.heal += agent.max_hp / 5
                agent.heal *= 2 if agent.type == "Butcher" else 1
            else:
                agent.heal += agent.max_hp / 10

            try:
                nyleptha = agent.get_acolyte("Nyleptha")
                object.damage *= 1 - nyleptha.get_effect_modifier(0) * .01
            except AttributeError:
                pass

        # ON_BIDE : Agents bides
        if agent.last_move == "Bide":
            if agent.type != "Boss":
                agent.attack *= 1.15
            else:
                agent.attack *= 1.05
                

        # GENERAL DAMAGE CALC
        if agent.type == "Boss" and object.type == "Leatherworker":
            # Leatherworkers get more defense in PvE
            agent.damage *= 0.85
        if agent.accessory.prefix == "Thorned":
            mult = Vars.ACCESSORY_BONUS["Thorned"][agent.accessory.type] / 100.0
            agent.damage += object.damage * mult # Thorned reflects damage

        # ON_COMBAT_END : After everything has been calculated
        try:
            onion = agent.get_acolyte("Onion")
            if self.turn == onion.get_effect_modifier(0):
                agent.crit *= 2
        except AttributeError:
            pass

        try:
            ajar = agent.get_acolyte("Ajar")
            agent.attack += ajar.get_effect_modifier(1)
            agent.current_hp -= ajar.get_effect_modifier(2)
        except AttributeError:
            pass

        try:
            lauren = agent.get_acolyte("Lauren")
            if object.damage < lauren.get_effect_modifier(1):
                agent.attack *= 1 + (lauren.get_effect_modifier(0) * .01)
        except AttributeError:
            pass

        try:
            thorp = agent.get_acolyte("Thorp")
            modifier = 1 + (thorp.get_effect_modifier(0) * .01)
            match random.randint(1, 4):
                case 1:
                    agent.attack *= modifier
                case 2:
                    agent.crit *= modifier
                case 3:
                    agent.current_hp *= modifier
                case 4:
                    agent.defense *= modifier
        except AttributeError:
            pass

        return agent, object

    @staticmethod
    def on_turn_end(player1 : Belligerent, player2 : Belligerent):
        return player1, player2