from discord.ext import commands

token = open(r"token.txt").read()

client = commands.Bot(command_prefix="/>")

cogFiles = ['commands.weather_commands', 'commands.music_commands']

for cog in cogFiles:
    client.load_extension(cog)
    print("%s has loaded. " % cog)

client.run(token)

