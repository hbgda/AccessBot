import re
from time import time
import math

from discord.ext import commands
from discord.message import Message
from discord.voice_client import VoiceClient
from discord_components.interaction import Interaction
from pyyoutube import Api as YTAPI
from pyyoutube.models.video import Video
from pyyoutube.models.playlist_item import PlaylistItem
from classes.MusicClasses import ServerMusicData, ServerMusicPlayer, Song
from helper_functions import format_str
from discord_components import Button, Select, SelectOption, ButtonStyle

yt_token = open(r"yt_api_key.txt").read()
yt_api = YTAPI(api_key=yt_token)


YTDL_OPTIONS = {'format': 'bestaudio'}
FFMPEG_OPTIONS = {
'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

players: dict[str, ServerMusicPlayer] = {}

class MusicCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="play")
    async def play_song(self, ctx: commands.Context, *, args: str = None):
        print(args)

        _addToQueue = False

        try:
            p = players[ctx.guild.id]
        except:
            p = None
        if p and p.serverMusicData.queue != []:
            print("_addToQueue = True")
            _addToQueue = True

        print(type(p))

        if p == None or p.vc.is_connected() == False:
            try:
                channel = ctx.author.voice.channel
                vc = await channel.connect()
                if p:
                    p.vc = vc
            except:
                await ctx.send("Join a voice channel!")
                return

        if p:
            player = p
        else:
            player = players[ctx.guild.id] = ServerMusicPlayer(ctx, vc, ServerMusicData([]), YTDL_OPTIONS)

        # I have no clue how regex works so this could be stupid but it seems to work so whatever
        if re.match("https://www\.youtube\.com/playlist\?list=([a-zA-Z]+([0-9]+[a-zA-Z]+)+)", args):  # Regex wasn't working properly idk: re.search("^(?!.*\?.*\bv=)https:\/\/www\.youtube\.com\/.*\?.*\blist=.*$", args):
            # Play playlist
            playlist_id = args.split("list=")[1].split("&")[0]
            print(playlist_id)

            await ctx.send("Getting links, depending on the size of the playlist this could take a while...")
            playlist_items: list[PlaylistItem] = yt_api.get_playlist_items(playlist_id=playlist_id, count=None).items
            print(len(playlist_items))

            for item in playlist_items:
                try:
                    song = Song(item.snippet.title.strip(), item.snippet.description, item.snippet.videoOwnerChannelTitle.strip(" - Topic"), item.snippet.thumbnails.high.url, "https://youtu.be/{0}".format(item.contentDetails.videoId), 0)
                    player.serverMusicData.add_song(song)
                except:
                    continue
                    

        elif re.search("^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+", args):
            # Play single
            video_id = args.split("=")
            if len(video_id) == 1:
                video_id = args.split("/")[-1]
                #print(video_id)
            else:
                video_id = video_id[1]
            print(video_id)
            video_info: Video = yt_api.get_video_by_id(video_id=video_id).items[0]
            #print(video_info)
        
            song = Song(video_info.snippet.title.strip(), video_info.snippet.description, video_info.snippet.channelTitle.strip(" - Topic"), video_info.snippet.thumbnails.high.url, args, (video_info.contentDetails.duration))
            player.serverMusicData.add_song(song)

        else:
            await ctx.send("Invalid URL.")
            return
            # TODO: Implement search

        if _addToQueue == True:
            await ctx.send("Added to queue!\nQueue length: {0}".format(len(player.serverMusicData.queue)))
            return

        await player.play_queue()
    
    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context, page = 1):
        selected_page = page

        try:
            player = players[ctx.guild.id]
        except:
            await ctx.send("Nothing playing!")
            return

        embed = player.get_queue_embed(page)

        time_token = str(time())
        msg: Message = await ctx.send(embed=embed, components=[
            [Button(style=ButtonStyle.blue, label="<<", custom_id=time_token),
            Button(style=ButtonStyle.blue, label="<", custom_id=time_token + "_1"),
            Button(style=ButtonStyle.blue, label=">", custom_id=time_token + "_2"),
            Button(style=ButtonStyle.blue, label=">>", custom_id=time_token + "_3")]
        ])

        while True:
            try:
                interaction: Interaction = await self.client.wait_for("button_click", timeout=60)
                if not (time_token in interaction.custom_id):
                    continue
                if interaction.component.label == "<<":
                    selected_page = 1
                    await msg.edit(embed=player.get_queue_embed())
                elif interaction.component.label == "<":
                    if selected_page > 1:
                        selected_page -= 1
                    await msg.edit(embed=player.get_queue_embed(selected_page))
                elif interaction.component.label == ">":
                    if selected_page < math.ceil(len(player.serverMusicData.queue)/5):
                        selected_page += 1
                    await msg.edit(embed=player.get_queue_embed(selected_page))
                elif interaction.component.label == ">>":
                    selected_page = math.ceil(len(player.serverMusicData.queue)/5)
                    await msg.edit(embed=player.get_queue_embed(selected_page))
                
                await interaction.respond(type=6)
            except:
                await msg.delete()
                return

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        p = players[ctx.guild.id]
        if type(p) != ServerMusicPlayer:
            await ctx.send("Nothing playing!")
        elif p.vc.is_paused():
            await ctx.send("Already paused!")
        else:
            p.pause()
            await ctx.send("Paused")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        p = players[ctx.guild.id]
        if type(p) != ServerMusicPlayer:
            await ctx.send("Nothing playing!")
        elif p.vc.is_playing():
            await ctx.send("Already playing!")
        else:
            p.resume()
            await ctx.send("Resumed")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context, index: int = None):
        p = players[ctx.guild.id]
        if type(p) != ServerMusicPlayer:
            await ctx.send("Nothing playing!")
        else:
            if index:
                p.serverMusicData.queueIndex += index - 1
            await p.play_next()

    @commands.command(name="prev")
    async def previous(self, ctx: commands.Context):
        p = players[ctx.guild.id]
        if type(p) != ServerMusicPlayer:
            await ctx.send("Nothing playing!")
        else:
            await p.play_prev()

    @commands.command(name="volume")
    async def volume(self, ctx: commands.Context, vol: float = 1):
        p = players[ctx.guild.id]
        if type(p) != ServerMusicPlayer:
            await ctx.send("Nothing playing!")
        else:
            p.set_volume(vol)

def setup(client):
    client.add_cog(MusicCommands(client))