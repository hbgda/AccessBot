import re

from discord.ext import commands
from discord.voice_client import VoiceClient
from pyyoutube import Api as YTAPI
from pyyoutube.models.video import Video
from pyyoutube.models.playlist_item import PlaylistItem
from classes.MusicClasses import ServerMusicData, ServerMusicPlayer, Song

yt_token = open(r"yt_api_key.txt").read()
yt_api = YTAPI(api_key=yt_token)


YTDL_OPTIONS = {'format': 'bestaudio'}
FFMPEG_OPTIONS = {
'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

servers: dict[str, ServerMusicData] = {}
players: dict[str, ServerMusicPlayer] = {}

class MusicCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="play")
    async def play_song(self, ctx: commands.Context, *, args: str = None):
        print(args)

        servers[ctx.guild.id] = ServerMusicData([])
        
        if re.search("^.*(youtu.be\/|list=)([^#\&\?]*).*", args):
            # Play playlist
            playlist_id = args.split("list=")[1].split("&")[0]
            print(playlist_id)

            await ctx.send("Getting links, depending on the size of the playlist this could take a while...")
            playlist_items: list[PlaylistItem] = yt_api.get_playlist_items(playlist_id=playlist_id, count=None).items
            print(len(playlist_items))

            for item in playlist_items:
                song = Song(item.snippet.title, item.snippet.description, item.snippet.channelTitle, item.snippet.thumbnails.default.url, "https://youtu.be/{0}".format(item.contentDetails.videoId), 0)
                servers[ctx.guild.id].add_song(song)

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
        
            song = Song(video_info.snippet.title.strip(), video_info.snippet.description, video_info.snippet.channelTitle, video_info.snippet.thumbnails.default.url, args, (video_info.contentDetails.duration))
            servers[ctx.guild.id].add_song(song)

        else:
            await ctx.send("Invalid URL.")
            return
            # TODO: Implement search

        channel = ctx.author.voice.channel
        
        vc = await channel.connect()
        smp = ServerMusicPlayer(ctx, vc, servers[ctx.guild.id], YTDL_OPTIONS)
        players[ctx.guild.id] = smp
        await smp.play_queue()

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