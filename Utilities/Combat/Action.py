from typing import Optional
import discord

from enum import Enum

from Utilities.ConfirmationMenu import PlayerOnlyView


class Action(Enum):
    DEFAULT = 0
    ATTACK = "🗡️"
    BLOCK = "\N{SHIELD}"
    PARRY = "\N{CROSSED SWORDS}"
    HEAL = "\u2764"
    BIDE = "\u23F1"


class InvalidAction(Exception):
    pass


class ActionView(PlayerOnlyView):
    def __init__(self, user: discord.Member):
        self._choice: Action = None
        super().__init__(user, timeout=30)

    @property
    def choice(self):
        return self._choice
    
    @choice.setter
    def choice(self, value: Action):
        if value not in Action:
            raise TypeError
        self._choice = value
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🗡️")
    async def attack(self, button: discord.ui.Button, 
            interaction: discord.Interaction):
        self.choice = Action.ATTACK

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\N{SHIELD}")
    async def block(self, button: discord.ui.Button, 
            interaction: discord.Interaction):
        self.choice = Action.BLOCK

    @discord.ui.button(style=discord.ButtonStyle.green, emoji="\N{CROSSED SWORDS}")
    async def parry(self, button: discord.ui.Button, 
            interaction: discord.Interaction):
        self.choice = Action.PARRY

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="\u2764")
    async def heal(self, button: discord.ui.Button, 
            interaction: discord.Interaction):
        self.choice = Action.HEAL

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\u23F1")
    async def bide(self, button: discord.ui.Button, 
            interaction: discord.Interaction):
        self.choice = Action.BIDE
