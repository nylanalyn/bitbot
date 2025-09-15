import random
from src import ModuleManager, utils

URL_WEATHER = "https://api.pirateweather.net/forecast"

# Predefined descriptions of locations from the Legacy of Kain series
NOSGOTH_LOCATIONS = [
    "The Pillars of Nosgoth, a majestic nexus of magic that binds the world.",
    "The ruins of Avernus Cathedral, a place of dark worship and mystery.",
    "Vorador's Mansion, a gothic refuge of vampires hidden in the depths of the woods.",
    "The Abyss, a foreboding chasm where Raziel met his transformation.",
    "Nupraptor's Retreat, a twisted fortress of madness atop a snowy peak.",
    "The spectral realm, a haunting reflection of the material world.",
    "The Silenced Cathedral, a vast structure built to end the vampiric scourge.",
    "The Termogent Forest, a dangerous and overgrown area of Nosgoth.",
    "The city of Meridian, a hub of human civilization struggling against decay."
]

class Module(ModuleManager.BaseModule):
    def _user_location(self, user):
        user_location = user.get_setting("location", None)
        if not user_location == None:
            name = user_location.get("name", None)
            return [user_location["lat"], user_location["lon"], name]

    @utils.hook("received.command.w", alias_of="weather")
    @utils.hook("received.command.weather")
    def weather(self, event):
        """
        :help: Get current weather for you or someone else
        :usage: [nickname]
        :require_setting: location
        :require_setting_unless: 1
        """
        api_key = self.bot.config["pirateweather-api-key"]

        location = None
        query = None
        nickname = None
        if event["args"]:
            query = event["args"]
            # Check if the user is requesting "nosgoth"
            if query.lower() == "nosgoth":
                description = random.choice(NOSGOTH_LOCATIONS)
                event["stdout"].write(f"Nosgoth: {description}")
                return
            
            if len(event["args_split"]) == 1 and event["server"].has_user_id(
                    event["args_split"][0]):
                target_user = event["server"].get_user(event["args_split"][0])
                location = self._user_location(target_user)
                if not location == None:
                    nickname = target_user.nickname
        else:
            location = self._user_location(event["user"])
            nickname = event["user"].nickname
            if location == None:
                raise utils.EventError("You don't have a location set")

        # Construct request URL and parameters
        if location is None and query:
            location_info = self.exports.get("get-location")(query)
            if location_info:
                location = [location_info["lat"], location_info["lon"],
                            location_info.get("name", None)]
        if location is None:
            raise utils.EventError("Unknown location")

        lat, lon, location_name = location
        url = f"{URL_WEATHER}/{api_key}/{lat},{lon}"
        args = {"units": "si"}  # Using SI units for metric output

        # Fetch weather data from Pirate Weather API
        page = utils.http.request(url, get_params=args).json()
        if page:
            if "currently" in page:
                location_str = location_name or f"{lat}, {lon}"

                celsius = f"{round(page['currently']['temperature'])}C"
                fahrenheit = f"{round(page['currently']['temperature'] * (9/5) + 32)}F"
                description = page["currently"]["summary"]
                humidity = f"{round(page['currently']['humidity'] * 100)}%"

                # Wind speed in km/h and mi/h
                wind_speed = page["currently"]["windSpeed"] * 3.6
                wind_speed_k = f"{round(wind_speed, 1)}km/h"
                wind_speed_m = f"{round(wind_speed * 0.6214, 1)}mi/h"

                if nickname:
                    location_str = f"({nickname}) {location_str}"

                event["stdout"].write(
                    f"{location_str} | {celsius}/{fahrenheit} | {description} | Humidity: {humidity} | Wind: {wind_speed_k}/{wind_speed_m}"
                )
            else:
                event["stderr"].write("No weather information for this location")
        else:
            raise utils.EventResultsError()
