import discord

class ConfirmationMenu(discord.ui.View):
    def __init__(self, author : discord.Member):
        self.author = author
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

    async def interaction_check(self, 
            interaction : discord.Interaction) -> bool:
        return interaction.user.id == self.author.id


class OfferMenu(ConfirmationMenu):
    def __init__(self, author : discord.Member, target : discord.Member):
        self.target = target
        super().__init__(author)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.target.id


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
        self.view.stop()