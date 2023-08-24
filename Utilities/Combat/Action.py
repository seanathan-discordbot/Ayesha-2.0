from typing import Optional
import discord

from enum import Enum

from discord.ui.item import Item


class Action(Enum):
    DEFAULT = 0
    ATTACK = 1
    BLOCK = 2
    PARRY = 3
    HEAL = 4
    BIDE = 5


class ActionView(discord.ui.View):
    def __init__(self, author_id: int):
        self.author_id = author_id
        self._choice: Action = None
        super().__init__(timeout=30)

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
