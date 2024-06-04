from enum import Enum, auto
import discord
import re
import asyncio
import json
import os
import encrypt as encryption
from datetime import datetime


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    SELECT_CATEGORY = auto()
    SELECT_SUB_CATEGORY = auto()
    CHOOSE_PROVIDE_GENERAL_CONTEXT = auto()
    CHOOSE_PROVIDE_CONTEXT = auto()
    PROVIDE_CONTEXT = auto()
    ASK_TO_BLOCK = auto()
    REPORT_COMPLETE = auto()
    REPORT_CANCEL = auto()

    MOD_DECIDE_INCITEMENT = auto()
    MOD_DECIDE_GENERAL_ABUSE = auto()
    MOD_CHECK_IMMINENT_DANGER = auto()
    MOD_CHECK_IMMINENT_DANGER_GENERAL = auto()
    MOD_CHOOSE_GENERAL_ABUSE = auto()
    MOD_SUBMIT_MESSAGE = auto()
    MOD_SELECT_VIOLATION = auto()
    MOD_WRITE_EXPLANATION = auto()
    MOD_DECIDE_INCITEMENT_ABUSE = auto()
    MOD_CHOOSE_BAN = auto()
    MOD_CHOOSE_BAN_DURATION = auto()
    MOD_TEMP_BAN_EXPLANATION = auto()
    MOD_PERMA_BAN_EXPLANATION = auto()
    MOD_INVESTIGATE = auto()
    MOD_CHOOSE_ESCALATE = auto()
    MOD_FINISH = auto()


class Reported_User:
    def __init__(self, reported_count, banned_count, violation_count, blocked_count):
        self.reported_count = reported_count
        self.banned_count = banned_count
        self.violation_count = violation_count
        self.blocked_count = blocked_count


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Reported_User):
            return obj.__dict__
        return super().default(obj)


class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.AWAITING_MESSAGE
        self.client = client
        self.reported_user = None
        self.encryption_key = b'\xa5\xd2^t\x00pp\xb7\xbc\xd1|\x1f\x05=\x81W\x10\xdf(A+\xdcK\xab\xd5 sE0\xe7\x1f,'
        self.summary = f'Report Summary: {datetime.now()} \n'

    async def handle_mod_message(self, message, reported_user):
        # Load global report history
        history_path = 'history.json'
        history = None
        if not os.path.isfile(history_path):
            raise Exception(f"{history_path} not found!")
        with open(history_path) as f:
            history = json.load(f)
        
        if reported_user:
            self.reported_user = encryption.encrypt(reported_user, self.encryption_key)
        
        if self.state == State.AWAITING_MESSAGE:
            self.reported_user = encryption.encrypt(reported_user, self.encryption_key)
            self.state = State.MOD_DECIDE_INCITEMENT
        
        if self.state == State.REPORT_START: 
            self.reported_user = encryption.encrypt(message.author.name, self.encryption_key)
            self.state = State.REPORT_COMPLETE

        if self.state == State.REPORT_COMPLETE:
            print("State is", self.state)

            reply = "\n \n" + \
                "Based on the report summary, is this report related to incitement of violence?"
            self.state = State.MOD_DECIDE_INCITEMENT
            return [reply]

        if self.state == State.MOD_DECIDE_INCITEMENT:
            print("State is", self.state)
            
            # Increment user report history: reported_count
            if self.reported_user not in history:
                history[self.reported_user] = Reported_User(1, 0, 0, 0)
            else:
                history[self.reported_user]['reported_count'] += 1

            # Save it back to json file
            with open(history_path, 'w') as file:
                json.dump(history, file, cls=CustomEncoder)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Based on the report summary above, do you find that this content violates our incitement to violence policy?"
                    self.state = State.MOD_DECIDE_INCITEMENT_ABUSE
                else:
                    reply = "Based on the report summary above, do you find that this content violates its category policy?"
                    self.state = State.MOD_DECIDE_GENERAL_ABUSE
                    
            return [reply]

        if self.state == State.MOD_DECIDE_GENERAL_ABUSE:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Is there an imminent danger to users where the legal escalation team should be involved?"

                    # Increment user report history: violation_count
                    if self.reported_user not in history:
                        history[self.reported_user] = Reported_User(1, 0, 1, 0)
                    else:
                        history[self.reported_user]['violation_count'] += 1

                    # Save it back to json file
                    with open(history_path, 'w') as file:
                        json.dump(history, file, cls=CustomEncoder)

                    self.state = State.MOD_CHECK_IMMINENT_DANGER_GENERAL

                else:
                    reply = "No action will be taken. Report complete."
                    self.state = State.MOD_FINISH

            return [reply]

        if self.state == State.MOD_CHECK_IMMINENT_DANGER_GENERAL:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Please write context to forward to the team. The initial flag will be included."
                    self.state = State.MOD_SUBMIT_MESSAGE
                else:
                    category_1 = "1: Harassment"
                    category_2 = "2: Spam"
                    category_3 = "3: Violent Content"
                    category_4 = "4: Hate speech or offsneive content"
                    category_5 = "5: Bullying or personal attacks"
                    category_6 = "6: Ilegal activity"
                    category_7 = "7: False information"
                    category_8 = "8: It's Obscene"
                    reply = "Please select the violated rule of the reported message:\n" + category_1 + "\n" + category_2 + "\n" + \
                            category_3 + "\n" + category_4 + "\n" + category_5 + "\n" + category_6 + "\n" + category_7 + \
                        "\n" + category_8
                    self.state = State.MOD_CHOOSE_GENERAL_ABUSE

            return [reply]

        if self.state == State.MOD_CHOOSE_GENERAL_ABUSE:
            print("State is", self.state)

            if message.content.lower() not in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                reply = "Please respond with a number"
            else:
                # Increment user report history: violation_count
                if self.reported_user not in history:
                    history[self.reported_user] = Reported_User(1, 0, 1, 0)
                else:
                    history[self.reported_user]['violation_count'] += 1

                # Save it back to json file
                with open(history_path, 'w') as file:
                    json.dump(history, file, cls=CustomEncoder)

                reply = "Please write an explanation for the reported user."
                self.state = State.MOD_WRITE_EXPLANATION

            return [reply]

        if self.state == State.MOD_DECIDE_INCITEMENT_ABUSE:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Is there an imminent danger to users where the legal escalation team should be involved?"

                    # Increment user report history: violation_count
                    if self.reported_user not in history:
                        history[self.reported_user] = Reported_User(1, 0, 1, 0)
                    else:
                        history[self.reported_user]['violation_count'] += 1
                        

                    # Save it back to json file
                    with open(history_path, 'w') as file:
                        json.dump(history, file, cls=CustomEncoder)

                    self.state = State.MOD_CHECK_IMMINENT_DANGER
                else:
                    reply = "No action will be taken. Report completed."
                    self.state = State.MOD_FINISH

            return [reply]

        if self.state == State.MOD_CHECK_IMMINENT_DANGER:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Please write context to forward to the team. The initial flag will be included."
                    self.state = State.MOD_SUBMIT_MESSAGE
                else:
                    category_1 = "1: Incites, promotes, or encourages acts of harm or violence."
                    category_2 = "2: Dogwhistle that incites violence."
                    category_3 = "3: Calls for war crimes or crimes against humanity."
                    reply = "Please select the violated rule: \n" + \
                        category_1 + "\n" + category_2 + "\n" + category_3
                    self.state = State.MOD_SELECT_VIOLATION

            return [reply]

        if self.state == State.MOD_SUBMIT_MESSAGE:
            print("State is", self.state)
            
            # Increment user report history: banned_count
            if self.reported_user not in history:
                history[self.reported_user] = Reported_User(1, 1, 1, 0)
            else:
                history[self.reported_user]['banned_count'] += 1
                
            # Save it back to json file
            with open(history_path, 'w') as file:
                json.dump(history, file, cls=CustomEncoder)

            reply = "Message submitted to team. Report completed. The user has been banned."
            self.state = State.MOD_FINISH
            return [reply]

        if self.state == State.MOD_SELECT_VIOLATION:
            print("State is", self.state)

            if message.content.lower() not in ["1", "2", "3"]:
                reply = "Please respond in numbers."
            else:
                reply = "Please write an explanation for the reported user."
                self.state = State.MOD_WRITE_EXPLANATION

            return [reply]

        if self.state == State.MOD_WRITE_EXPLANATION:
            print("State is", self.state)

            choice_1 = "1: Yes"
            choice_2 = "2: Investigate More"
            choice_3 = "3: No"
            reply = "Post removed. Ban the reported user? \n" + \
                choice_1 + "\n" + choice_2 + "\n" + choice_3
            self.state = State.MOD_CHOOSE_BAN

            return [reply]

        if self.state == State.MOD_CHOOSE_BAN:
            print("State is", self.state)

            if message.content not in ["1", "2", "3"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content == "1":
                    reply = "1: One week\n2: Permanent"
                    self.state = State.MOD_CHOOSE_BAN_DURATION
                elif message.content == "2":
                    user = encryption.decrypt(self.reported_user, self.encryption_key)
                    reported_count = history[self.reported_user]['reported_count']
                    banned_count = history[self.reported_user]['banned_count']
                    violation_count = history[self.reported_user]['violation_count']
                    blocked_count = history[self.reported_user]['blocked_count']
                    reply = f"The user {user} has been:\n" + f"Reported {reported_count} times\n" + \
                        f"Violated policy {violation_count} times\n" + f"Blocked {blocked_count} times\n" + \
                            f"Banned {banned_count} times\n \n" + "What would you like to do?\n" + \
                        "1: Ban user\n" + "2: Escalate Report\n" + "3: Do not ban user\n"
                    self.state = State.MOD_INVESTIGATE
                else:
                    reply = f"{encryption.decrypt(self.reported_user, self.encryption_key)} will not be banned. Report completed."
                    self.state = State.MOD_FINISH

            return [reply]

        if self.state == State.MOD_INVESTIGATE:
            print("State is", self.state)

            if message.content not in ["1", "2", "3"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content == "1":
                    self.state = State.MOD_CHOOSE_BAN_DURATION
                    reply = "1: One week\n2: Permanent"
                elif message.content == "2":
                    self.state = State.MOD_CHOOSE_ESCALATE
                    reply = "Confirm escalation?"
                else:
                    self.state = State.MOD_FINISH
                    reply = f"{encryption.decrypt(self.reported_user, self.encryption_key)} will not be banned. Report completed"

                return [reply]

        if self.state == State.MOD_CHOOSE_BAN_DURATION:
            print("State is", self.state)

            # Increment user report history: banned_count
            if self.reported_user not in history:
                history[self.reported_user] = Reported_User(1, 1, 1, 0)
            else:
                history[self.reported_user]['banned_count'] += 1

            # Save it back to json file
            with open(history_path, 'w') as file:
                json.dump(history, file, cls=CustomEncoder)

            if message.content not in ["1", "2"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content == "1":
                    reply = "Please add an explanation for the user as to why they're being temporarily banned."
                    self.state = State.MOD_TEMP_BAN_EXPLANATION
                else:
                    reply = "Please add an explanation for the user as to why they're being permanently banned."
                    self.state = State.MOD_PERMA_BAN_EXPLANATION

            return [reply]

        if self.state == State.MOD_TEMP_BAN_EXPLANATION:
            print("State is", self.state)

            reply = f"{encryption.decrypt(self.reported_user, self.encryption_key)} has been banned for one week. Report completed."
            self.state = State.MOD_FINISH

            return [reply]

        if self.state == State.MOD_PERMA_BAN_EXPLANATION:
            print("State is", self.state)

            reply = f"{encryption.decrypt(self.reported_user, self.encryption_key)} has been banned permanently. Escalate report to another team?"
            self.state = State.MOD_CHOOSE_ESCALATE

            return [reply]

        if self.state == State.MOD_CHOOSE_ESCALATE:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond with yes or no."
            else:
                if message.content.lower() == "yes":
                    reply = "The report has been escalated. Report completed."
                else:
                    reply = "Reported completed."
                self.state = State.MOD_FINISH

            return [reply]

    async def handle_message(self, message):
        history_path = 'history.json'
        history = None
        if not os.path.isfile(history_path):
            raise Exception(f"{history_path} not found!")
        with open(history_path) as f:
            history = json.load(f)

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCEL
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

            self.state = State.MESSAGE_IDENTIFIED


        if self.state == State.MESSAGE_IDENTIFIED:
            print("State is", self.state)
            category_1 = "1: Harassment"
            category_2 = "2: Spam"
            category_3 = "3: Violent Content"
            category_4 = "4: Hate speech or offsneive content"
            category_5 = "5: Bullying or personal attacks"
            category_6 = "6: Ilegal activity"
            category_7 = "7: False information"
            category_8 = "8: It's Obscene"
            reply = "I found this message:" + "```" + message.author.name + ": " + message.content + "```" + \
                "Please select what the message is in violation of:\n" + category_1 + "\n" + category_2 + "\n" + \
                    category_3 + "\n" + category_4 + "\n" + category_5 + "\n" + category_6 + "\n" + category_7 + \
                "\n" + category_8
            self.reported_user = encryption.encrypt(message.author.name, self.encryption_key)
            self.state = State.SELECT_CATEGORY
            self.summary += "Reported Message: "+ "```" + message.author.name + ": " + message.content + "```"

            return [reply]


        if self.state == State.SELECT_CATEGORY:
            print("State is", self.state)

            if message.content not in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content != "3":
                    general_message = "We’re sorry that you’ve experienced this content. Can you provide more context on your reasons for reporting this message?"
                    if message.content == "1":
                        reply = "You've selected Harassment. " + general_message
                        self.summary += "Category: Harassment \n"
                    elif message.content == "2":
                        reply = "You've selected Spam. " + general_message
                        self.summary += "Category: Spam \n"
                    elif message.content == "4":
                        reply = "You've selected Hate speech or offensive content. " + general_message
                        self.summary += "Category: Offensive Content \n"
                    elif message.content == "5":
                        reply = "You've selected Bullying or personal attacks. " + general_message
                        self.summary += "Category: Bullying or Personal Attacks \n"
                    elif message.content == "6":
                        reply = "You've selected Illegal activity. " + general_message
                        self.summary += "Category: Illegal Activity \n"
                    elif message.content == "7":
                        reply = "You've selected False information. " + general_message
                        self.summary += "Category: False Information \n"
                    else:
                        reply = "You've selected It's obscene. " + general_message
                        self.summary += "Category: Obscenity \n"
                    self.state = State.CHOOSE_PROVIDE_GENERAL_CONTEXT
                else:
                    sub_category_1 = "1: Incitement to violence"
                    sub_category_2 = "2: Glorification of violence"
                    sub_category_3 = "3: Threat of harm to oneself or others"
                    reply = "Please tell us how which type of violent content you believe the message is in violation of from the following list: " + \
                            "\n" + sub_category_1 + "\n" + sub_category_2 + "\n" + sub_category_3
                    self.state = State.SELECT_SUB_CATEGORY

                # Increment user report history: reported_count
                if self.reported_user not in history:
                    history[self.reported_user] = Reported_User(1, 0, 0, 0)
                else:
                    history[self.reported_user]['reported_count'] += 1

                # Save it back to json file
                with open(history_path, 'w') as file:
                    json.dump(history, file, cls=CustomEncoder)

            return [reply]

        if self.state == State.SELECT_SUB_CATEGORY:
            print("State is", self.state)

            if message.content not in ["1", "2", "3"]:
                reply = "Please select from the provided list with numbers."
            else:
                if message.content == "1":
                    reply = "We’re sorry that you’ve experienced this content. Can you provide more context on your reasons for reporting this message?"
                    self.state = State.CHOOSE_PROVIDE_CONTEXT
                    self.summary += "Category: Violent Content (Incitement to Violence) \n"
                elif message.content == "2":
                    reply = "We’re sorry that you’ve experienced this content. Can you provide more context on your reasons for reporting this message?"
                    self.state = State.CHOOSE_PROVIDE_CONTEXT
                    self.summary += "Category: Violent Content (Glorification of Violence) \n"
                else:
                    reply = f"If this is an emergency, please dial 911. Your report has been submitted to the moderation team for immediate action. Would you like to block [{encryption.decrypt(self.reported_user, self.encryption_key)}]?"
                    self.state = State.ASK_TO_BLOCK
                    self.summary += "Category: Violent Content (Threat of Harm of Oneself or Others) \n"

            return [reply]

        if self.state == State.CHOOSE_PROVIDE_GENERAL_CONTEXT:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "Please provide additional context about the abuse you are reporting."
                    self.state = State.PROVIDE_CONTEXT
                else:
                    reply = f"Thank you for reporting this message. The moderation team has been informed of your report and will review it as quickly as possible. Would you like to block [{encryption.decrypt(self.reported_user, self.encryption_key)}]?"
                    self.state = State.ASK_TO_BLOCK

            return [reply]

        if self.state == State.CHOOSE_PROVIDE_CONTEXT:
            print("State is", self.state)

            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in Yes or No."
            else:
                if message.content.lower() == "yes":
                    reply = "You’ve indicated this message is inciting violence. Please provide more context. As a reminder, we remove content under our Incitement to Violence guidelines if it:" + "\n" \
                        + "-Incites, promotes, or encourages acts of harm or violence" + "\n" + "-Dogwhistles that indirectly incite violence" + "\n" + "-Calls for war crimes or crimes against humanity" \
                            + "\n \n" + "If there is an immediate threat, please contact emergency services immediately."
                    self.state = State.PROVIDE_CONTEXT
                else:
                    reply = f"Your report has been sumbitted for review. Would you like to block [{encryption.decrypt(self.reported_user, self.encryption_key)}]?"
                    self.state = State.ASK_TO_BLOCK

            return [reply]

        if self.state == State.PROVIDE_CONTEXT:
            print("State is", self.state)
            reply = f"Thank you for reporting this message. The moderation team has been informed of your report and will review it as quickly as possible. Would you like to block [{encryption.decrypt(self.reported_user, self.encryption_key)}]?"
            self.state = State.ASK_TO_BLOCK
            self.summary += f"User provided context: {message.content} \n"

            return [reply]

        if self.state == State.ASK_TO_BLOCK:
            print("State is", self.state)
            if message.content.lower() not in ["yes", "no"]:
                reply = "Please respond in yes or no."
            else:
                if message.content.lower() == "yes":
                    reply = f"{encryption.decrypt(self.reported_user, self.encryption_key)} has been blocked. Thank you for keeping our community safe. Have a good day!"
                    # Increment user report history: blocked_count
                    if self.reported_user not in history:
                        history[self.reported_user] = Reported_User(1, 0, 0, 1)
                    else:
                        history[self.reported_user]['blocked_count'] += 1

                    # Save it back to json file
                    with open(history_path, 'w') as file:
                        json.dump(history, file, cls=CustomEncoder)

                    self.state = State.REPORT_COMPLETE
                    self.summary += "Block reported user: Yes \n"
                else:
                    reply = "Thank you for keeping our community safe. Have a good day!"
                    self.state = State.REPORT_COMPLETE
                    self.summary += "Block reported user: No\n"

            return [reply]

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE

    def report_cancel(self):
        return self.state == State.REPORT_CANCEL
    
    def mod_flow_complete(self):
        return self.state == State.MOD_FINISH
