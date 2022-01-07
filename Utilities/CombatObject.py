import discord

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
    def __init__(self, name : str, bell_type : str, attack : int, crit : int,
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
        bell_type : str
            'Player' or 'Boss'
        attack : int
            The attack stat
        crit : int
            The crit chance stat
        hp : int
            The maximum/starting HP value
        defense : int
            The defense stat
        disc_id : Optional[int]
            If bell_type is 'Player', pass the person's Discord ID
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
        self.type = bell_type
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
            name, "Player", attack, crit, hp, defense, disc_id, weapon, helmet,
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



class CombatInstance:
    def perform_attack(self, attacker : Belligerent, defender : Belligerent):
        damage_reduction = (100.0 - defender.defense) / 100.0
        damage = int(attacker.attack * damage_reduction)
        defender.current_hp -= damage
        return f"{attacker.name} dealt {damage} damage to {defender.name}!"





class CombatMenu(discord.ui.View):
    """A view specifically made for PvE.    
    """
    def __init__(self, author : discord.Member, player1 : Belligerent,
            player2 : Belligerent):
        super().__init__(timeout=30.0)
        self.author = author
        self.player1 = player1
        self.player2 = player2
        self.combat_instance = CombatInstance()
        self.turn_counter = 1
        self.embed = None

    @discord.ui.button(label="Attack", style=discord.ButtonStyle.green)
    async def attack(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        turn = self.combat_instance.perform_attack(self.player1, self.player2)
        await self.update(interaction, turn)

    # @discord.ui.button(label="Crit", style=discord.ButtonStyle.green)
    # async def crit(self, button : discord.ui.Button, 
    #         interaction : discord.Interaction):
    #     self.output += "You crit\n"
    #     await self.update(interaction)

    def update_embed(self):
        self.embed = discord.Embed(
            title=f"{self.player1.name} vs. {self.player2.name}",
            color=Vars.ABLUE)
        self.embed.add_field(
            name=f"{self.player1.name}'s Stats",
            value = (
                f"ATK: `{self.player1.attack}`\n"
                f"CRIT: `{self.player1.crit}%`\n"
                f"HP: `{self.player1.current_hp}`\n"
                f"DEF: `{self.player1.defense}`\n"))
        self.embed.add_field(
            name=f"{self.player2.name}'s Stats",
            value = (
                f"ATK: `{self.player2.attack}`\n"
                f"CRIT: `{self.player2.crit}%`\n"
                f"HP: `{self.player2.current_hp}`\n"
                f"DEF: `{self.player2.defense}`\n"))
        self.embed.add_field(
            name="Your move", value=f"Turn `{self.turn_counter}`", inline=False)

    async def update(self, interaction : discord.Interaction, turn : str):
        if self.player2.current_hp <= 0:
            await interaction.response.edit_message(content="You win", embed=None)
        else:
            self.update_embed()
            await interaction.response.edit_message(embed=self.embed)
            self.turn_counter += 1

    async def interaction_check(self, 
            interaction : discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

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