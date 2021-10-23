from os import name
import discord
from discord.colour import Color
from discord.ext import commands
import requests
import json


apiKey = open(r"weather_api_key.txt").read()

class WeatherCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.command(name="weather")
    async def getWeatherDefault(self, ctx: commands.Context, *, args: str = "No args!"):
        print(args)

        requestURL = "http://api.openweathermap.org/data/2.5/weather?q=" + args + "&units=metric&APPID=" + apiKey.strip()
        print(requestURL)
        jsonStr = requests.get(requestURL).content.decode("utf-8")
        #print(jsonStr)
        weatherData = json.loads(s=jsonStr)
        print(json.dumps(obj=weatherData, sort_keys=True, indent=4))

        embed = discord.Embed(title="Weather Data")

        if str(weatherData['cod']) != "200":
            embed.description = "Error: " + weatherData["cod"]
            embed.add_field(name="Message", value=weatherData["message"], inline=False)
            embed.colour = 0xFF0000
            await ctx.send(content="Command Syntax:\n`city name` or\n`city name, state code` or\n`city name, state code, country code`", embed=embed)
            return

        icon = weatherData["weather"][0]["icon"]
        main = weatherData["main"]

        embed.set_thumbnail(url="http://openweathermap.org/img/wn/{0}@2x.png".format(icon))

        w_name = weatherData["name"]
        w_country = (weatherData["sys"]["country"] if "country" in weatherData["sys"] else "None")
        w_description = weatherData["weather"][0]["description"]
        w_description = w_description[0].upper() + w_description[1: ]

        embed.description = "{0}, {1}\n{2}".format(w_name, w_country, w_description)
        
        embed.add_field(name="Temperature", value=str(main["temp"]) + "°C", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Feels Like", value=str(main["feels_like"]) + "°C", inline=True)

        embed.add_field(name="Min Temp", value=str(main["temp_min"]) + '°C', inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Max Temp", value=str(main["temp_max"]) + '°C', inline=True)

        embed.add_field(name="Humidity", value=str(main["humidity"]) + "%", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Pressure", value=str(main["pressure"]) + "mb", inline=True)

        embed.colour = 0x00FF00

        await ctx.send(embed=embed)

        



def setup(client):
    client.add_cog(WeatherCommands(client))
