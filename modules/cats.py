#--depends-on commands
#--depends-on config

import random, re, time
from src import EventManager, ModuleManager, utils

CATS = ["・゜゜・。。・゜゜^..^ Meoooow!"]

DEFAULT_MIN_MESSAGES = 100

@utils.export("channelset", utils.BoolSetting("cats-enabled",
    "Whether or not to spawn cats"))
@utils.export("channelset", utils.IntRangeSetting(50, 200, "cats-min-messages",
    "Minimum messages between cats spawning"))
@utils.export("channelset", utils.BoolSetting("cats-kick",
    "Whether or not to kick someone talking to non-existent cats"))
@utils.export("channelset", utils.BoolSetting("cats-prevent-highlight",
    "Whether or not to prevent highlighting users with !buddies/!thieves"))
class Module(ModuleManager.BaseModule):
    @utils.hook("new.channel")
    def new_channel(self, event):
        self.bootstrap_channel(event["channel"])

    def bootstrap_channel(self, channel):
        if not hasattr(channel, "cat_active"):
            channel.cat_active = None
            channel.cat_lines = 0

    def _activity(self, channel):
        self.bootstrap_channel(channel)

        cats_enabled = channel.get_setting("cats-enabled", False)

        if (cats_enabled and
                not channel.cat_active and
                not channel.cat_lines == -1):
            channel.cat_lines += 1
            min_lines = channel.get_setting("cats-min-messages",
                DEFAULT_MIN_MESSAGES)

            if channel.cat_lines >= min_lines:
                show_cat = random.SystemRandom().randint(1, 20) == 1

                if show_cat:
                    self._trigger_cat(channel)

    @utils.hook("command.regex")
    @utils.kwarg("expect_output", False)
    @utils.kwarg("ignore_action", False)
    @utils.kwarg("command", "cat-trigger")
    @utils.kwarg("pattern", re.compile(".+"))
    def channel_message(self, event):
        self._activity(event["target"])

    def _trigger_cat(self, channel):
        channel.cat_lines = -1
        delay = random.SystemRandom().randint(5, 20)
        self.timers.add("cat", self._send_cat, delay, channel=channel)

    def _send_cat(self, timer):
        channel = timer.kwargs["channel"]
        channel.cat_active = time.time()
        channel.cat_lines = 0
        channel.send_message(random.choice(CATS))

    def _cat_action(self, channel, user, action, setting):
        cat_timestamp = channel.cat_active
        channel.set_setting("cat-last", time.time())
        channel.cat_active = None

        user_id = user.get_id()
        action_count = channel.get_user_setting(user_id, setting, 0)
        action_count += 1
        channel.set_user_setting(user_id, setting, action_count)

        seconds = round(time.time()-cat_timestamp, 2)

        cats_plural = "cat" if action_count == 1 else "cats"

        return "%s %s a cat in %s seconds! You've %s %d %s in %s!" % (
            user.nickname, action, seconds, action, action_count, cats_plural,
            channel.name)

    def _no_cat(self, channel, user, stderr):
        message = "There was no cat!"
        cat_timestamp = channel.get_setting("cat-last", None)
        if not cat_timestamp == None:
            seconds = round(time.time()-cat_timestamp, 2)
            message += " missed by %s seconds" % seconds

        if channel.get_setting("cats-kick"):
            channel.send_kick(user.nickname, message)
        else:
            stderr.write("%s: %s" % (user.nickname, message))

    @utils.hook("received.command.pet", alias_of="lick")
    @utils.hook("received.command.pur", alias_of="lick")
    @utils.hook("received.command.lick")
    @utils.kwarg("help", "Befriend a cat")
    @utils.spec("!-channelonly")
    def lick(self, event):
        if event["target"].cat_active:
            action = self._cat_action(event["target"], event["user"],
                "buddied", "cats-buddied")
            event["stdout"].write(action)
        else:
            self._no_cat(event["target"], event["user"], event["stderr"])
    
    @utils.hook("received.command.fry", alias_of="steal")
    @utils.hook("received.command.steal")
    @utils.kwarg("help", "Trap a cat")
    @utils.spec("!-channelonly")
    def steal(self, event):
        if event["target"].cat_active:
            action = self._cat_action(event["target"], event["user"],
                "trapped", "cats-stolen")
            event["stdout"].write(action)
        else:
            self._no_cat(event["target"], event["user"], event["stderr"])

    def _target(self, target, is_channel, query):
        if query:
            if not query == "*":
                return query
        elif is_channel:
            return target.name

    @utils.hook("received.command.buddies")
    @utils.kwarg("help", "Show top 10 cat buddies")
    @utils.spec("?<channel>word")
    def buddies(self, event):
        query = self._target(event["target"], event["is_channel"],
            event["spec"][0])

        stats = self._top_cat_stats(event["server"], event["target"],
            "cats-buddied", "buddies", query)
        event["stdout"].write(stats)
    @utils.hook("received.command.stolen")
    @utils.kwarg("help", "Show top 10 cat thieves")
    @utils.spec("?<channel>word")
    def thieves(self, event):
        query = self._target(event["target"], event["is_channel"],
            event["spec"][0])

        stats = self._top_cat_stats(event["server"], event["target"],
            "cats-stolen", "thieves", query)
        event["stdout"].write(stats)

    def _top_cat_stats(self, server, target, setting, description,
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
        return "Top cat %s%s: %s" % (description, channel_query_str,
            ", ".join(top_10))

    def _get_nickname(self, server, target, nickname):
        nickname = server.get_user(nickname).nickname
        if target.get_setting("cats-prevent-highlight", True):
            nickname = utils.prevent_highlight(nickname)
        return nickname

    @utils.hook("received.command.catstats")
    @utils.kwarg("help", "Get yours, or someone else's, cat stats")
    @utils.spec("?<nickname>ouser")
    def catstats(self, event):
        target_user = event["spec"][0] or event["user"]

        befs = target_user.get_channel_settings_per_setting(
            "cats-buddied")
        traps = target_user.get_channel_settings_per_setting("cats-stolen")

        all = [(chan, val, "bef") for chan, val in befs]
        all += [(chan, val, "trap") for chan, val in traps]

        current = {"bef": 0, "trap": 0}
        overall = {"bef": 0, "trap": 0}

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
            current_str = " (%d/%d in %s)" % (current["bef"],
                current["trap"], event["target"].name)

        event["stdout"].write(
            "%s has buddied %d and trapped %d cats%s" %
            (target_user.nickname, overall["bef"], overall["trap"],
            current_str))

    @utils.hook("received.command.confess")
    @utils.kwarg("help", "Confess to stealing a cat")
    @utils.spec("!-channelonly")
    def confess(self, event):
        user_id = event["user"].get_id()
        channel = event["target"]
        trapped_cats = channel.get_user_setting(user_id, "cats-stolen")
        if trapped_cats and trapped_cats > 0:
            trapped_cats -= 1
            channel.set_user_setting(user_id, "cats-stolen", trapped_cats)
            event["stdout"].write("%s released a cat!" % event["user"].nickname)
            self._trigger_cat(channel)
        else:
            event["stderr"].write("You don't have any trapped cats!")

    @utils.hook("received.command.lose")
    @utils.kwarg("help", "Let a cat loose")
    @utils.spec("!-channelonly")
    def lose(self, event):
        user_id = event["user"].get_id()
        channel = event["target"]
        buddied_cats = channel.get_user_setting(user_id, "cats-buddied")
        if buddied_cats and buddied_cats > 0:
            buddied_cats -= 1
            channel.set_user_setting(user_id, "cats-buddied", buddied_cats)
            event["stdout"].write("%s freed a cat!" % event["user"].nickname)
            self._trigger_cat(channel)
        else:
            event["stderr"].write("You don't have any friendly cats!")
