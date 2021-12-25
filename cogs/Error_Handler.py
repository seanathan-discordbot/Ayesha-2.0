import discord
from discord.commands.errors import ApplicationCommandInvokeError
from discord.ext import commands

import sys
import traceback

from discord.ui.item import Item

from Utilities import Checks

class Error_Handler(commands.Cog):
    """Bot error handler."""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Error Handling activated.")

    # --- ERROR HANDLER ---
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        print_traceback = True

        # --- CHARACTER RELATED ---
        if isinstance(error, Checks.HasChar):
            message = (f"You already have a character.\nFor help, read the "
                       f"`/tutorial` or go to the `/support` server.")
            await ctx.respond(message)
            print_traceback = False

        if isinstance(error, ApplicationCommandInvokeError):
            if isinstance(error.original, Checks.PlayerHasNoChar):
                message = ("This player does not have a character. "
                           "Ask them to make one \:)")
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.ExcessiveCharacterCount):
                message = (f"Your response exceeded the character limit.\n"
                            f"Please keep your response under `"
                            f"{error.original.limit}` characters.")
                await ctx.respond(message)
                print_traceback = False

        # --- ARGUMENT ERRORS ---
        if isinstance(error, Checks.ExcessiveCharacterCount):
            message = (f"Your response exceeded the character limit.\nPlease "
                       f"keep your response under `{error.limit}` characters.")
            await ctx.respond(message)
            print_traceback = False

        if print_traceback:
            traceback.print_exception(
                error.__class__, error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(Error_Handler(bot))