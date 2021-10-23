from discord.ext import commands
from discord_components import DiscordComponents


token = open(r"token.txt").read()

client = commands.Bot(command_prefix="/>")
DiscordComponents(client)

cogFiles = ['commands.weather_commands', 'commands.music_commands', 'commands.test_commands']

for cog in cogFiles:
    client.load_extension(cog)
    print("%s has loaded. " % cog)

client.run(token)


