import threading, random, time
from datetime import datetime, timedelta
from src import EventManager, ModuleManager, utils

MESSAGES = [
    "I'm absolutely swamped with animals here!",
    "Too many critters, I can't keep up!",
    "Animals everywhere, I'm overwhelmed!",
    "I feel like I'm in a zoo, so many animals!",
    "Help! The animals are taking over!",
    "I'm drowning in a sea of animals!",
    "So many animals, I don't know where to start!",
    "Animals, animals, animals... I'm overwhelmed!",
    "I can't handle all these animals at once!",
    "The animal invasion is too much for me!",
]

class Module(ModuleManager.BaseModule):
    def monthly_yell(bot, channel):
        while True:
            now = datetime.now()
            # Calculate the next month
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
            # Random offset in days within the next month (0-29)
            days_offset = random.randint(0, 29)
            yell_time = next_month + timedelta(days=days_offset)
            # Random offset in seconds within the day
            seconds_offset = random.randint(0, 86399)
            yell_time += timedelta(seconds=seconds_offset)
            # Sleep until the random time
            sleep_seconds = (yell_time - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            # Send the message
            message = random.choice(MESSAGES)
            bot.say(channel, message)

    def setup(bot):
        channel = "#transience"  # Replace with your channel
        t = threading.Thread(target=monthly_yell, args=(bot, channel), daemon=True)
        t.start()
