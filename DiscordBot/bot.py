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
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    tokens = json.load(f)
    discord_token = tokens['discord']

# Takes in two strings, a and b, and returns a hashed version of the joined string. The hash is deterministic.
def hash(a, b):
    joined = a + b
    hash_object = hashlib.sha256()
    hash_object.update(joined.encode('utf-8'))

    return hash_object.hexdigest()


class ModBot(discord.Client):
    def __init__(self):
        self.report_time = datetime.now()
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.reports = {}  # Map from reported user id + reported message to the report against them
        self.mod_channel = None
        self.author_id = None
        self.reported_message = None
        self.current_report_key = None # hashing reported user id and reported message together as the key for report
        self.report_identified = False # -------> flags
        self.count = 0 # -----------------------> flags
        self.mod_in_progress = False # ---------> flags
        self.author_name = None # Name of reported author to be passed into report.py, needed for storing report history

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
            if message.channel.name == 'group-3':
                await self.handle_channel_message(message)
            else:
                if self.count > 0:
                    # Handle initial starting state
                    if message.content == "start":
                        # Using GPT-4o, determine the next most important report to handle
                        self.current_report_key = self.get_next_key()
                        self.mod_in_progress = True
                        # Forward report summary to mod channel
                        for r in self.reports[self.current_report_key][2]:
                            await self.mod_channel.send(r)
                        
                        # Manually ask this question in the mod channel
                        reply = "\n \n" + "Based on the report summary, is this report related to incitement of violence?"
                        for r in [reply]:
                            await self.mod_channel.send(r)
                    # Report already started on the moderator end, call handle_mod_channel()  
                    elif self.mod_in_progress and message.content != "start":
                        await self.handle_mod_channel(message)
        else:
            await self.handle_dm(message)

    
    # This grabs all reported messages from self.reports, puts them into a list and asks GPT-4o to return the most
    # urgent one that needs to be reviewed. Returns the key to the report
    def get_next_key(self):
        reported_messages = []
        # Add all reported messages to a list
        for key in self.reports:
            reported_messages.append(self.reports[key][1])
        
        # If GPT behaves as asked, it will return the exact message that has the highest priority
        top_priority = openai.rank_priority(reported_messages)
        
        # Find its corresponding key
        for key in self.reports:
            if top_priority == self.reports[key][1]:    
                return key
             

    async def handle_mod_channel(self, message):
        responses = await self.reports[self.current_report_key][0].handle_mod_message(message, self.author_name)
        for r in responses:
            await self.mod_channel.send(r)

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

        # Only respond to messages if they're part of a reporting flow
        if self.current_report_key not in self.reports and not message.content.startswith(Report.START_KEYWORD) and not self.report_identified:
            return

        if message.content.startswith(Report.START_KEYWORD):
            reply = "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            for r in [reply]:
                await message.channel.send(r)
            
        # Add active report only when the message and reported user is identified
        if self.current_report_key not in self.reports and self.report_identified:
            self.reports[self.current_report_key] = [Report(self), self.reported_message]
            
        if self.report_identified:

            responses = await self.reports[self.current_report_key][0].handle_message(message)
            for r in responses:
                await message.channel.send(r)

            # If the report is complete or cancelled, remove it from our map
            if self.reports[self.current_report_key][0].report_complete():
                self.report_identified = False
                # Generate report symmary ##### CHANGED
                self.reports[self.current_report_key].append([self.reports[self.current_report_key][0].summary])
                self.count += 1

            # If report canceled during the process, pop the report from map and set flags accordingly.
            if self.reports[self.current_report_key][0].report_cancel() or message.content.lower() == "cancel":
                self.report_identified = False
                self.reports.pop(self.current_report_key)
        

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        mod_channel = self.mod_channels[message.guild.id]
        self.mod_channel = mod_channel

        incitement_flag = self.eval_text(message.content)

        if incitement_flag:
            self.author_name = message.author.name
            self.author_id = message.author.id
            self.reported_message = message.content
            self.current_report_key = hash(str(self.author_id), self.reported_message)

            if self.current_report_key not in self.reports:
                self.reports[self.current_report_key] = [Report(self), self.reported_message, self.code_format(message)]   
            self.count += 1

    # Wrapper function for classify_message in openai_classify.py, currently set to return true always. 
    def eval_text(self, message):
        return openai.classify_message(message)

    def code_format(self, message):
        result = "The message  by" + "```" + message.author.name + ": " + message.content + "```" + "was evaluated to be in violation of " + \
            "content policy against incitement of violence speech."
        return [result]


client = ModBot()
client.run(discord_token)