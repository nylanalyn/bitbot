#--depends-on commands
#--depends-on config

from src import ModuleManager, utils

@utils.export("set", utils.Setting("species", "Set your species",
    example="Lawnmower"))
class Module(ModuleManager.BaseModule):
    @utils.hook("received.command.species")
    def species(self, event):
        """
        :help: Get your, or someone else's, species
        :usage: [nickname]
        :require_setting: species
        :require_setting_unless: 1
        """
        target_user = event["user"]
        if event["args"]:
            target_user = event["server"].get_user(event["args_split"][0])

        species = target_user.get_setting("species", None)

        if not species == None:
            event["stdout"].write("Species for %s: %s" %
                (target_user.nickname, species))
        else:
            event["stderr"].write("No species set for %s" %
                target_user.nickname)
