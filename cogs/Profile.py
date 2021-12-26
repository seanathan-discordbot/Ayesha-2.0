import discord
from discord.commands.commands import Option

from discord.ext import commands, pages

from Utilities import Checks, Vars, PlayerObject, Analytics

class ConfirmButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10.0)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.grey)
    async def decline(self, button : discord.ui.Button, 
            interaction : discord.Interaction):
        self.value = False
        self.stop()

class Profile(commands.Cog):
    """Create a character and view your stats!"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Profile is ready.")

    # AUXILIARY METHODS
    async def view_profile(self, ctx, player : discord.Member):
        profile = await PlayerObject.get_player_by_id(
            await self.bot.db.acquire(),
            player.id)

        embed = discord.Embed(
            title=f"{player.display_name}'s Profile: {profile.char_name}",
            color=Vars.ABLUE)
        embed.set_thumbnail(url=player.avatar.url)
        embed.add_field(
            name="Character Info",
            value=(
                f"Gold: `{profile.gold}`\nOccupation: `{profile.occupation}`"
                f"\nOrigin: `{profile.origin}`\nLocation: `{profile.location}`"
                f"\nAssociation: `{profile.assc.name} (ID: {profile.assc.id})` "
            ),
            inline=True)
        embed.add_field(
            name="Character Stats",
            value=(
                f"Level: `{profile.level}`\nGravitas: `{profile.gravitas}`\n"
                f"Attack: `{profile.get_attack()}`\nCrit: "
                f"`{profile.get_crit()}%`\nHP: `{profile.get_hp()}`\n"),
            inline=True)
        embed.add_field(
            name="Party",
            value=(
                f"Item: `{profile.equipped_item.name} "
                f"({profile.equipped_item.rarity})`\nAcolyte: "
                f"`{profile.acolyte1.acolyte_name} ("
                f"{profile.acolyte1.gen_dict['Rarity']}⭐)`\nAcolyte: "
                f"`{profile.acolyte2.acolyte_name} ("
                f"{profile.acolyte2.gen_dict['Rarity']}⭐)`"),
                inline=True)

        await ctx.respond(embed=embed)

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.not_player)
    async def start(self, ctx, 
            name: Option(str, description="Your character's name",
                required=False, default=None)):
        """Start the game of Ayesha."""
        if not name:
            name = ctx.author.name
        if len(name) > 32:
            raise Checks.ExcessiveCharacterCount(limit=32)

        embed = discord.Embed(
            title="Start the game of Ayesha?",
            color=Vars.ABLUE)
        embed.add_field(
            name=f"Your Name: {name}",
            value=(f"You can customize your name by redoing this command with "
                   f"the `name` parameter filled!"))
        view = ConfirmButton()
        msg = await ctx.respond(embed=embed, view=view)
        await view.wait()
        if view.value is None:
            await ctx.respond("Timed out.")
        elif view.value:
            await PlayerObject.create_character(
                await self.bot.db.acquire(),
                ctx.author.id,
                name
            )
            await ctx.respond(f"Started the game: {name}")
        else:
            await ctx.respond(f"You cancelled :(")
        await msg.delete_original_message()

    @commands.slash_command(name="profile", guild_ids=[762118688567984151])
    async def self_profile(self, ctx):
        """View your profile."""
        await self.view_profile(ctx, ctx.author)

    @commands.user_command(name="View Profile", guild_ids=[762118688567984151])
    async def other_profile(self, ctx, member: discord.Member):
        await self.view_profile(ctx, member)

    @commands.slash_command(guild_ids=[762118688567984151])
    async def new_profile(self, ctx):
        """View your profile (New Version)."""
        await ctx.defer()

        # Load information
        player = ctx.author
        profile = await PlayerObject.get_player_by_id(
            await self.bot.db.acquire(),
            player.id)
        level, dist = profile.get_level(get_next=True)
        gold_rank = Analytics.stringify_rank(
            await Analytics.get_gold_rank(
                await self.bot.db.acquire(), player.id)
        )
        gravitas_rank = Analytics.stringify_rank(
            await Analytics.get_gravitas_rank(
                await self.bot.db.acquire(), player.id)
        )
        xp_rank = Analytics.stringify_rank(
            await Analytics.get_xp_rank(
                await self.bot.db.acquire(), player.id)
        )
        boss_rank = Analytics.stringify_rank(
            await Analytics.get_bosswins_rank(
                await self.bot.db.acquire(), player.id)
        )
        pvp_rank = Analytics.stringify_rank(
            await Analytics.get_pvpwins_rank(
                await self.bot.db.acquire(), player.id)
        )

        # Create pages
        page1 = discord.Embed(            
            title=f"Character Information: {profile.char_name}",
            color=Vars.ABLUE
        )
        page1.set_thumbnail(url=player.avatar.url)
        page1.add_field(name="Experience",
            value=(
                f"Level: `{level}`\n"
                f"EXP: `{profile.xp}` (`{xp_rank}`)\n"
                f"To Next Level: `{dist}`"),
            inline=True)
        page1.add_field(name="Wealth",
            value=(
                f"Gold: `{profile.gold}` (`{gold_rank}`)\n"
                f"Gravitas: `{profile.gravitas}` (`{gravitas_rank}`)"),
            inline=True)
        page1.add_field(name="Lore",
            value=(
                f"Occupation: `{profile.occupation}`\n"
                f"Origin: `{profile.origin}`\n"
                f"Location: `{profile.location}`\n"
                f"Association: `{profile.assc.name}` "
                f"(ID: `{profile.assc.id}`)"),
            inline=False)

        page2 = discord.Embed(            
            title=f"Combat Loadout: {profile.char_name}",
            color=Vars.ABLUE
        )
        page2.set_thumbnail(url=player.avatar.url)
        page2.add_field(name="General",
            value=(
                f"Attack: `{profile.get_attack()}`\n"
                f"Crit Chance: `{profile.get_crit()}`\n"
                f"Hit Points: `{profile.get_hp()}`"),
            inline=True)
        page2.add_field(name="Reputation",
            value=(
                f"Bosses Defeated: `{profile.boss_wins}` (`{boss_rank}`)\n"
                f"Pvp Wins: `{profile.pvp_wins}` (`{pvp_rank}`)\n"),
            inline=True)
        page2.add_field(name=f"Equips",
            value=(
                f"{profile.equipped_item.type}: {profile.equipped_item.name} "
                f"({profile.equipped_item.rarity}, `"
                f"{profile.equipped_item.attack}` ATK, `"
                f"{profile.equipped_item.crit}` CRIT)"
            ),
            inline=False)
        page2.add_field(name="Acolyte",
            value=(
                f"{profile.acolyte1.acolyte_name} (`"
                f"{profile.acolyte1.gen_dict['Rarity']}⭐`)"
            ),
            inline=True)
        page2.add_field(name="Acolyte",
            value=(
                f"{profile.acolyte2.acolyte_name} (`"
                f"{profile.acolyte2.gen_dict['Rarity']}⭐`)"
            ),
            inline=True)

        # page3 = discord.Embed(
        #     title=f"{player.display_name}'s Profile: {profile.char_name}",
        #     color=Vars.ABLUE)
        # page3.set_thumbnail(url=player.avatar.url)
        # page3.add_field(
        #     name="Party",
        #     value=(
        #         f"Item: `{profile.equipped_item.name} "
        #         f"({profile.equipped_item.rarity})`\nAcolyte: "
        #         f"`{profile.acolyte1.acolyte_name} ("
        #         f"{profile.acolyte1.gen_dict['Rarity']}⭐)`\nAcolyte: "
        #         f"`{profile.acolyte2.acolyte_name} ("
        #         f"{profile.acolyte2.gen_dict['Rarity']}⭐)`"),
        #         inline=True)

        # Output pages
        paginator = pages.Paginator(pages=[page1, page2], timeout=30)
        paginator.customize_button("next", button_label=">", button_style=discord.ButtonStyle.green)
        paginator.customize_button("prev", button_label="<", button_style=discord.ButtonStyle.green)
        paginator.customize_button("first", button_label="<<", button_style=discord.ButtonStyle.blurple)
        paginator.customize_button("last", button_label=">>", button_style=discord.ButtonStyle.blurple)
        await paginator.send(ctx, ephemeral=False)

        

    # @commands.slash_command(guild_ids=[762118688567984151])
    # async def gold(self, ctx):
    #     """See how much gold you have."""
    #     player = await PlayerObject.get_player_by_id(
    #         await self.bot.db.acquire(),
    #         ctx.author.id
    #     )

    #     await ctx.respond(f"You have `{player.gold}` gold.")

    # @commands.slash_command(guild_ids=[762118688567984151])
    # async def level(self, ctx):
    #     """See your current, level, xp, and distance from levelling up."""
    #     player = await PlayerObject.get_player_by_id(
    #         await self.bot.db.acquire(),
    #         ctx.author.id
    #     )
    #     level, dist = player.get_level(get_next=True)

    #     embed = discord.Embed(color=Vars.ABLUE)
    #     embed.add_field(name="Level", value=level)
    #     embed.add_field(name="EXP", value=player.xp)
    #     embed.add_field(name=f"EXP until Level {level+1}", value=dist)
    #     await ctx.respond(embed=embed)

    @commands.slash_command(guild_ids=[762118688567984151])
    async def rename(self, ctx, *, 
            name : Option(str, description="Your new name", required=True)):
        """Change your character's name."""
        player = await PlayerObject.get_player_by_id(
            await self.bot.db.acquire(),
            ctx.author.id
        )
        await player.set_char_name(await self.bot.db.acquire(), name)
        await ctx.respond(f"You changed your name to **{name}**.")

    # TODO: Add tutorial; this should probably go last



def setup(bot):
    bot.add_cog(Profile(bot))