from enum import Enum, auto
import discord
import re
import asyncio


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    SELECT_CATEGORY = auto()
    SELECT_SUB_CATEGORY = auto()
    CHOOSE_PROVIDE_CONTEXT = auto()
    PROVIDE_CONTEXT = auto()
    ASK_TO_BLOCK = auto()
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
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED

        if self.state == State.MESSAGE_IDENTIFIED:
            print("State is", self.state)
            category_1 = "1: Harassment"
            category_2 = "2: Spam"
            category_3 = "3: Violent Content"
            reply = "I found this message:" + "```" + message.author.name + ": " + message.content + "```" + \
                "Please select what the message is in violation of:\n" + \
                    category_1 + "\n" + category_2 + "\n" + category_3
            self.state = State.SELECT_CATEGORY
            return [reply]

        if self.state == State.SELECT_CATEGORY:
            print("State is", self.state)

            if message.content not in ["1", "2", "3"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content == "1":
                    reply = "You've selected Harassment"
                elif message.content == "2":
                    reply = "You've selected Spam"
                else:
                    sub_category_1 = "1: Incitement to violence"
                    sub_category_2 = "2: Glorification of violence"
                    sub_category_3 = "3: Threat of harm to oneself or others"
                    reply = "Please tell us how which type of violent content you believe the message is in violation of from the following list: " + \
                            "\n" + sub_category_1 + "\n" + sub_category_2 + "\n" + sub_category_3
                self.state = State.SELECT_SUB_CATEGORY
            return [reply]

        if self.state == State.SELECT_SUB_CATEGORY:
            print("State is", self.state)

            if message.content not in ["1", "2", "3"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content == "1":
                    reply = "Would you like to tell us why you think the message is an incitement to violence?"
                    self.state = State.CHOOSE_PROVIDE_CONTEXT
                elif message.content == "2":
                    reply = "Would you like to tell us why you think the message is a glorication of violence?"
                    self.state = State.CHOOSE_PROVIDE_CONTEXT
                else:
                    reply = "If this is an emergency, please dial 911. Your report has been submitted to the moderation team for immediate action. Would you like to block this user?"
                    self.state = State.ASK_TO_BLOCK
            return [reply]

        if self.state == State.CHOOSE_PROVIDE_CONTEXT:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Please give us any additional context to help our team better identify abuse."
                    self.state = State.PROVIDE_CONTEXT
                else:
                    reply = "Your report has been sumbitted for review. Would you like to block this user?"
                    self.state = State.ASK_TO_BLOCK
            return [reply]

        if self.state == State.PROVIDE_CONTEXT:
            print("State is", self.state)
            # Logic for storing context somewhere

            #
            reply = "Thank you for providing additional context to our team. Your report has been sumbitted for review. Would you like to block this user?"
            self.state = State.ASK_TO_BLOCK
            return [reply]

        if self.state == State.ASK_TO_BLOCK:
            print("State is", self.state)
            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in yes or no."
            else:
                if message.content.lower() == "yes":
                    reply = "The user has been blocked. Thank you for keeping our community safe. Have a good day!"
                    self.state = State.REPORT_COMPLETE
                else:
                    reply = "Thank you for keeping our community safe. Have a good day!"
                    self.state = State.REPORT_COMPLETE
            return [reply]

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
