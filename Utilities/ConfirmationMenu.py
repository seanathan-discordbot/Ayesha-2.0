import discord

class PlayerOnlyView(discord.ui.View):
    def __init__(self, user : discord.Member, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id


class ConfirmationMenu(PlayerOnlyView):
    def __init__(self, user : discord.Member, *args, **kwargs):
        super().__init__(user=user, *args, **kwargs)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, row=4)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        self.stop()

class LockedConfirmationMenu(PlayerOnlyView):
    def __init__(self, user : discord.Member, custom_id : str, *args, **kwargs):
        super().__init__(user=user, *args, **kwargs)
        self.custom_id = custom_id
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        interaction.custom_id = self.custom_id
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, row=4)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        interaction.custom_id = self.custom_id
        self.stop()

class OneButtonView(discord.ui.View):
    """Creates a view with one button to press"""
    def __init__(self, label : str, author : discord.Member, 
            author_only : bool = True, timeout : float = 30.0):
        """
        Parameters
        ----------
        label : str
            What will be printed on the button
        author : discord.Member
            The user whose command invoked this object
        author_only : bool
            True if only the author can interact with this view
        timeout : float
            Time in seconds until view times out
        """
        self.label = label
        self.author = author
        self.author_only = author_only
        super().__init__(timeout=timeout)
        self.value = False
        self.add_item(OneButton(label))

    async def interaction_check(self, 
            interaction : discord.Interaction) -> bool:
        if self.author_only:
            return interaction.user.id == self.author.id
        return True

class OneButton(discord.ui.Button):
    def __init__(self, label : str):
        super().__init__(label=label)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = True
        await interaction.response.edit_message(content=None)
        self.view.stop()