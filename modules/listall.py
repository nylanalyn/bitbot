#--depends-on commands

from src import ModuleManager, utils

class Module(ModuleManager.BaseModule):
    @utils.hook("received.command.listall")
    @utils.kwarg("help", "List all of your animals")
    @utils.spec("?<nickname>word")
    def listall(self, event):
        """
        A command to list all animals a user has collected.
        """
        nickname = event["spec"][0]
        if nickname:
            target_user = event["server"].get_user(nickname)
            if not target_user or not hasattr(target_user, 'get_channel_settings_per_setting'):
                event["stderr"].write(f"I don't know any user named '{nickname}'.")
                return
        else:
            target_user = event["user"]

        # Ducks
        ducks_befriended = target_user.get_channel_settings_per_setting("ducks-befriended")
        ducks_trapped = target_user.get_channel_settings_per_setting("ducks-shot")
        total_ducks_befriended = sum(count for _, count in ducks_befriended)
        total_ducks_trapped = sum(count for _, count in ducks_trapped)

        # Cats
        cats_buddied = target_user.get_channel_settings_per_setting("cats-buddied")
        cats_stolen = target_user.get_channel_settings_per_setting("cats-stolen")
        total_cats_buddied = sum(count for _, count in cats_buddied)
        total_cats_stolen = sum(count for _, count in cats_stolen)

        # Puppies
        puppies_cuddled = target_user.get_channel_settings_per_setting("puppies-buddied")
        puppies_caged = target_user.get_channel_settings_per_setting("puppies-caged")
        total_puppies_cuddled = sum(count for _, count in puppies_cuddled)
        total_puppies_caged = sum(count for _, count in puppies_caged)


        event["stdout"].write(
            f"{target_user.nickname} has: "
            f"{total_ducks_befriended} befriended ducks, {total_ducks_trapped} trapped ducks, "
            f"{total_cats_buddied} buddied cats, {total_cats_stolen} stolen cats, "
            f"{total_puppies_cuddled} cuddled puppies, and {total_puppies_caged} caged puppies."
        )
