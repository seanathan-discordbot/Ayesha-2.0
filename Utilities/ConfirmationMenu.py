import discord

class ConfirmationMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30.0)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.grey, row=4)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        self.stop()