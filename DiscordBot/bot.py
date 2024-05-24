# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
import pdb
from datetime import datetime

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


def parse_list(input_list):
    # Join the characters into a single string
    joined_string = ''.join(input_list)

    # Split the string into a list of strings
    string_list = joined_string.split(',')

    # Remove any '[' or ']' characters from the strings
    cleaned_list = [s.replace('[', '').replace(']', '')
                    for s in string_list]

    return cleaned_list


class ModBot(discord.Client):
    def __init__(self):
        self.report_time = datetime.now()
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.reports = {}  # Map from user IDs to the state of their report
        self.report_summary = ["Report Summary " + f"({self.report_time}): \n"]
        self.mod_channel = None
        self.author_id = None
        self.mod_flag = False

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception(
                "Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

        if self.mod_flag:
            await self.handle_mod_channel(message)

    async def handle_mod_channel(self, message):

        responses = await self.reports[self.author_id].handle_mod_message(message)
        for r in responses:
            await self.mod_channel.send(r)

        if self.reports[self.author_id].mod_flow_complete():
            self.mod_flag = False
            self.reports.pop(self.author_id)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply = "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return
        author_id = message.author.id
        self.author_id = author_id
        responses = []

        # Forwarding logic
        m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
        if m:
            guild_id = int(m.group(1))
            self.mod_channel = self.mod_channels[guild_id]

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        self.report_summary += "User: " + message.content + "\n \n"

        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        self.report_summary += "Bot: " + str(responses) + "\n \n"
        self.report_summary = parse_list(self.report_summary)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            self.report_summary = [self.report_summary[0].replace('\\n', '\n')]
            # SEND TO MOD CHANNEL INSTEAD
            for c in self.report_summary:
                await self.mod_channel.send(c)
            self.mod_flag = True

            self.report_summary = [
                "Report Summary " + f"({self.report_time}): \n"]

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(message)
        # scores = self.eval_text(message.content)
        # await mod_channel.send(self.code_format(scores))

    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text + "'"


client = ModBot()
client.run(discord_token)
