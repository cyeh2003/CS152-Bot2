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
import openai_classify as openai
import hashlib

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


def hash(a, b):
    joined = a + b
    hash_object = hashlib.sha256()
    hash_object.update(joined.encode('utf-8'))

    return hash_object.hexdigest()


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
        self.report_identified = False
        self.reported_message = None
        self.current_report_key = None
        self.count = 0
        self.mod_in_progress = False
        self.author_name = None

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

        if self.count > 0:
            if message.content == "start":
                self.current_report_key = self.get_next_key()
                self.mod_in_progress = True
                # send report summary to mod channel, how current_report_key is determined is TODO
                for r in self.reports[self.current_report_key][2]:
                    await self.mod_channel.send(r)
                print("hit here")
                reply = "\n \n" + "Based on the report summary, is this report related to incitement of violence?"
                for r in [reply]:
                    await self.mod_channel.send(r)
            elif self.mod_in_progress and message.content != "start":
                await self.handle_mod_channel(message)
    
    def get_next_key(self):
        reported_messages = []
        for key in self.reports:
            # append message to reported_message list
            print(self.reports[key])
            reported_messages.append(self.reports[key][1])
            
        top_priority = openai.rank_priority(reported_messages)
        
        for key in self.reports:
            if top_priority == self.reports[key][1]:    
                return key
             

    async def handle_mod_channel(self, message):
        print("hit handle mod channel")
        responses = await self.reports[self.current_report_key][0].handle_mod_message(message, self.author_name)
        print(self.reports[self.current_report_key][0])
        if responses:
            for r in responses:
                await self.mod_channel.send(r)
        else:
            return

        if self.reports[self.current_report_key][0].mod_flow_complete():
            self.mod_in_progress = False
            self.count -= 1
            for r in [f"There are {self.count} reports to be reviewed."]:
                await self.mod_channel.send(r)
            self.reports.pop(self.current_report_key)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply = "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        responses = []

        # Forwarding logic
        m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
        if m:
            guild_id = int(m.group(1))
            guild = discord.Client.get_guild(self, int(m.group(1)))
            channel = guild.get_channel(int(m.group(2)))
            self.mod_channel = self.mod_channels[guild_id]
            reported_message = await channel.fetch_message(int(m.group(3)))
            self.author_id = reported_message.author.id
            self.report_identified = True
            self.reported_message = reported_message.content
            self.current_report_key = hash(str(self.author_id), self.reported_message)
            print(self.current_report_key)

        # Only respond to messages if they're part of a reporting flow
        if self.current_report_key not in self.reports and not message.content.startswith(Report.START_KEYWORD) and not self.report_identified:
            print("we hit break")
            return

        if message.content.startswith(Report.START_KEYWORD):
            reply = "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            for r in [reply]:
                await message.channel.send(r)
        
            
        # Add active report only when the message and reported user is identified.
        if self.current_report_key not in self.reports and self.report_identified:
            self.reports[self.current_report_key] = [Report(self), self.reported_message]
            
        if self.report_identified:
            self.report_summary += "User: " + message.content + "\n \n"

            # Let the report class handle this message; forward all the messages it returns to uss
            responses = await self.reports[self.current_report_key][0].handle_message(message)
            for r in responses:
                await message.channel.send(r)

            self.report_summary += "Bot: " + str(responses) + "\n \n"
            self.report_summary = parse_list(self.report_summary)

            # If the report is complete or cancelled, remove it from our map
            if self.reports[self.current_report_key][0].report_complete():
                self.report_identified = False
                self.report_summary = [self.report_summary[0].replace('\\n', '\n')]
                # Gather report symmary
                self.reports[self.current_report_key].append(self.report_summary)

                self.mod_ready = True
                self.count += 1
                self.report_summary = ["Report Summary " + f"({self.report_time}): \n"]

            if self.reports[self.current_report_key][0].report_cancel() or message.content.lower() == "cancel":
                self.report_summary = ["Report Summary " + f"({self.report_time}): \n"]
                self.report_identified = False
                self.reports.pop(self.current_report_key)
        

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        self.mod_channel = mod_channel
        incitement_flag = self.eval_text(message.content)
        print(incitement_flag)

        if incitement_flag:
            self.author_name = message.author.name
            self.author_id = message.author.id
            self.reported_message = message.content
            self.current_report_key = hash(str(self.author_id), self.reported_message)

            if self.current_report_key not in self.reports:
                self.reports[self.current_report_key] = [Report(self), self.reported_message, self.code_format(message)]
                
            self.count += 1
            self.mod_ready = True

    def eval_text(self, message):
        return openai.classifyMessage(message)

    def code_format(self, message):
        result = "The message  by" + "```" + message.author.name + ": " + message.content + "```" + "was evaluated to be in violation of " + \
            "content policy against incitement of violence speech."
        return [result]


client = ModBot()
client.run(discord_token)
