#--depends-on commands
#--depends-on config

import random, re, time
from src import EventManager, ModuleManager, utils

puppies = ["・゜゜・。。・゜゜ ૮₍ 𝁽ܫ𝁽 ₎ა fscking ruff"]

DEFAULT_MIN_MESSAGES = 100

@utils.export("channelset", utils.BoolSetting("puppies-enabled",
    "Whether or not to spawn puppies"))
@utils.export("channelset", utils.IntRangeSetting(50, 200, "puppies-min-messages",
    "Minimum messages between puppies spawning"))
@utils.export("channelset", utils.BoolSetting("puppies-kick",
    "Whether or not to kick someone talking to non-existent puppies"))
@utils.export("channelset", utils.BoolSetting("puppies-prevent-highlight",
    "Whether or not to prevent highlighting users with !cuddle/!cage"))
class Module(ModuleManager.BaseModule):
    @utils.hook("new.channel")
    def new_channel(self, event):
        self.bootstrap_channel(event["channel"])

    def bootstrap_channel(self, channel):
        if not hasattr(channel, "pup_active"):
            channel.pup_active = None
            channel.pup_lines = 0

    def _activity(self, channel):
        self.bootstrap_channel(channel)

        puppies_enabled = channel.get_setting("puppies-enabled", False)

        if (puppies_enabled and
                not channel.pup_active and
                not channel.pup_lines == -1):
            channel.pup_lines += 1
            min_lines = channel.get_setting("puppies-min-messages",
                DEFAULT_MIN_MESSAGES)

            if channel.pup_lines >= min_lines:
                show_pup = random.SystemRandom().randint(1, 20) == 1

                if show_pup:
                    self._trigger_pup(channel)

    @utils.hook("command.regex")
    @utils.kwarg("expect_output", False)
    @utils.kwarg("ignore_action", False)
    @utils.kwarg("command", "pup-trigger")
    @utils.kwarg("pattern", re.compile(".+"))
    def channel_message(self, event):
        self._activity(event["target"])

    def _trigger_pup(self, channel):
        channel.pup_lines = -1
        delay = random.SystemRandom().randint(5, 20)
        self.timers.add("pup", self._send_pup, delay, channel=channel)

    def _send_pup(self, timer):
        channel = timer.kwargs["channel"]
        channel.pup_active = time.time()
        channel.pup_lines = 0
        channel.send_message(random.choice(puppies))

    def _pup_action(self, channel, user, action, setting):
        pup_timestamp = channel.pup_active
        channel.set_setting("pup-last", time.time())
        channel.pup_active = None

        user_id = user.get_id()
        action_count = channel.get_user_setting(user_id, setting, 0)
        action_count += 1
        channel.set_user_setting(user_id, setting, action_count)

        seconds = round(time.time()-pup_timestamp, 2)

        puppies_plural = "pup" if action_count == 1 else "puppies"

        return "%s %s a pup in %s seconds! You've %s %d %s in %s!" % (
            user.nickname, action, seconds, action, action_count, puppies_plural,
            channel.name)

    def _no_pup(self, channel, user, stderr):
        message = "There was no pup!"
        pup_timestamp = channel.get_setting("pup-last", None)
        if not pup_timestamp == None:
            seconds = round(time.time()-pup_timestamp, 2)
            message += " missed by %s seconds" % seconds

        if channel.get_setting("puppies-kick"):
            channel.send_kick(user.nickname, message)
        else:
            stderr.write("%s: %s" % (user.nickname, message))

    @utils.hook("received.command.cuddle")
    @utils.kwarg("help", "Befriend a pup")
    @utils.spec("!-channelonly")
    def lick(self, event):
        if event["target"].pup_active:
            action = self._pup_action(event["target"], event["user"],
                "buddied", "puppies-buddied")
            event["stdout"].write(action)
        else:
            self._no_pup(event["target"], event["user"], event["stderr"])

    @utils.hook("received.command.cage")
    @utils.kwarg("help", "Trap a pup")
    @utils.spec("!-channelonly")
    def steal(self, event):
        if event["target"].pup_active:
            action = self._pup_action(event["target"], event["user"],
                "trapped", "puppies-caged")
            event["stdout"].write(action)
        else:
            self._no_pup(event["target"], event["user"], event["stderr"])

    def _target(self, target, is_channel, query):
        if query:
            if not query == "*":
                return query
        elif is_channel:
            return target.name

    @utils.hook("received.command.puppies")
    @utils.kwarg("help", "Show top 10 pup buddies")
    @utils.spec("?<channel>word")
    def buddies(self, event):
        query = self._target(event["target"], event["is_channel"],
            event["spec"][0])

        stats = self._top_pup_stats(event["server"], event["target"],
            "puppies-buddied", "puppies", query)
        event["stdout"].write(stats)
    @utils.hook("received.command.caged")
    @utils.kwarg("help", "Show top 10 pup cagers")
    @utils.spec("?<channel>word")
    def cagers(self, event):
        query = self._target(event["target"], event["is_channel"],
            event["spec"][0])

        stats = self._top_pup_stats(event["server"], event["target"],
            "puppies-caged", "cagers", query)
        event["stdout"].write(stats)

    def _top_pup_stats(self, server, target, setting, description,
            channel_query):
        channel_query_str = ""
        if not channel_query == None:
            channel_query = server.irc_lower(channel_query)
            channel_query_str = " in %s" % channel_query

        stats = server.find_all_user_channel_settings(setting)

        user_stats = {}
        for channel, nickname, value in stats:
            if not channel_query or channel_query == channel:
                if not nickname in user_stats:
                    user_stats[nickname] = 0
                user_stats[nickname] += value

        top_10 = utils.top_10(user_stats,
            convert_key=lambda n: self._get_nickname(server, target, n))
        return "Top pup %s%s: %s" % (description, channel_query_str,
            ", ".join(top_10))

    def _get_nickname(self, server, target, nickname):
        nickname = server.get_user(nickname).nickname
        if target.get_setting("puppies-prevent-highlight", True):
            nickname = utils.prevent_highlight(nickname)
        return nickname

    @utils.hook("received.command.pupstats")
    @utils.kwarg("help", "Get yours, or someone else's, pup stats")
    @utils.spec("?<nickname>ouser")
    def puppiestats(self, event):
        target_user = event["spec"][0] or event["user"]

        befs = target_user.get_channel_settings_per_setting(
            "puppies-buddied")
        traps = target_user.get_channel_settings_per_setting("puppies-caged")

        all = [(chan, val, "cuddle") for chan, val in befs]
        all += [(chan, val, "cage") for chan, val in traps]

        current = {"cuddle": 0, "cage": 0}
        overall = {"cuddle": 0, "cage": 0}

        if event["is_channel"]:
            for channel_name, value, action in all:
                if not action in overall:
                    overall[action] = 0
                overall[action] += value

                if event["is_channel"]:
                    channel_name_lower = event["server"].irc_lower(channel_name)
                    if channel_name_lower == event["target"].name:
                        current[action] = value

        current_str = ""
        if current:
            current_str = " (%d/%d in %s)" % (current["cuddle"],
                current["cage"], event["target"].name)

        event["stdout"].write(
            "%s has cuddled %d and caged %d puppies%s" %
            (target_user.nickname, overall["cuddle"], overall["cage"],
            current_str))

    @utils.hook("received.command.unlock")
    @utils.kwarg("help", "unlock a caged pup")
    @utils.spec("!-channelonly")
    def confess(self, event):
        user_id = event["user"].get_id()
        channel = event["target"]
        trapped_puppies = channel.get_user_setting(user_id, "puppies-caged")
        if trapped_puppies and trapped_puppies > 0:
            trapped_puppies -= 1
            channel.set_user_setting(user_id, "puppies-caged", trapped_puppies)
            event["stdout"].write("%s released a pup!" % event["user"].nickname)
            self._trigger_pup(channel)
        else:
            event["stderr"].write("You don't have any trapped puppies!")

    @utils.hook("received.command.kiss")
    @utils.kwarg("help", "Let a pup loose")
    @utils.spec("!-channelonly")
    def lose(self, event):
        user_id = event["user"].get_id()
        channel = event["target"]
        buddied_puppies = channel.get_user_setting(user_id, "puppies-buddied")
        if buddied_puppies and buddied_puppies > 0:
            buddied_puppies -= 1
            channel.set_user_setting(user_id, "puppies-buddied", buddied_puppies)
            event["stdout"].write("%s freed a pup!" % event["user"].nickname)
            self._trigger_pup(channel)
        else:
            event["stderr"].write("You don't have any friendly puppies!")
