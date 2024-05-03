from enum import Enum, auto
import discord
import re
import asyncio


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()


class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None

    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]

        if self.state == State.REPORT_START:
            reply = "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]

        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                fetched_message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED

        if self.state == State.MESSAGE_IDENTIFIED:
            print("State is MESSAGE_IDENTIFIED")
            category_1 = "1"
            category_2 = "2"
            category_3 = "3"
            reply = "I found this message:" + "```" + fetched_message.author.name + ": " + fetched_message.content + "```" + \
                "Please select what the message is in violation of:\n" + \
                    category_1 + "\n" + category_2 + "\n" + category_3
            await message.channel.send(reply)

            def check(m):
                return m.channel == message.channel

            try:
                response = await self.client.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await message.channel.send('Sorry, you took too long to respond.')
            else:
                while response.content not in ["1", "2", "3"]:
                    await message.channel.send('Please select from the provided list')
                    response = await self.client.wait_for('message', check=check, timeout=60.0)

                if response.content == "1":
                    await message.channel.send('You selected option 1.')
                    r = "Please provide further context"
                    await message.channel.send(r)
                    context = await self.client.wait_for('message', check=check, timeout=60.0)
                    await message.channel.send('You said "' + context.content + '", Thank you.')
                elif response.content == "2":
                    await message.channel.send('You selected option 2.')
                elif response.content == "3":
                    await message.channel.send('You selected option 3.')

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
