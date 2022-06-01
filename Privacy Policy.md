# Ayesha Bot Privacy Policy

## Stored Information

Ayesha's overarching goal is to be as lightweight as possible and require as little information and privileges as needed. This includes not using any of Discord's privileged intents. The bot, for example, cannot read anything posted in channels that it is in unless the bot is specifically mentioned or is part of an Application Command (e.g. slash command). 

The bot does store this information that may be considered valuable:
* Each user's unique Discord ID (as accessed in Developer Tools)
* Each user's character's name, which defaults to their Discord username, but can be changed with the `/rename command`.
    * Former names are not stored.
* Each user's nickname (the display name they have in a server), should they play a game from our `/wordchain` module.

All other information is largely character-specific or randomly-generated. The database schema can be found on the GitHub repository under the `Database` directory.

With the exception of fields stored by Discord (e.g. unique user ID), all other information can be changed and deleted through the use of their corresponding bot command.

## Usage of Data
The bot uses the stored data only for the execution of its commands.
This data is stored privately and is unavailable to any third party.

## Temporarily Stored Data
As we do not use any of Discord's Privileged Intents, we do not store any temporary data. We cannot read server info, server members, or member info unless as part of a specific command. That data is stored in memory for the lifetime of that command's execution.

## Removal of Data
Stored data can be removed and updated by using their corresponding command (e.g. change your character's name with the `/rename` command).

A manual deletion of your character and all corresponding information linked to your Discord account can be requested by joining the [support server](https://discord.gg/FRTTARhN44) and contacting a server admin.

Note that this bot is global to all servers (i.e. the character you make in Server A will remain with you should you play the bot in Server B), and leaving the server the bot is in or removing the bot from servers you are in will not affect your character in any way.