from typing import Any
import discord
from discord import guild
from discord import voice_client
from discord.channel import VoiceChannel
from discord.ext import commands
from discord.voice_client import VoiceClient
from pyyoutube.models import video
from pyyoutube.models.playlist_item import PlaylistItem, PlaylistItemListResponse
import requests
import time
import os
import re
import asyncio

from threading import Timer
from youtube_dl import YoutubeDL
from classes.MusicClasses import ServerMusicData, Song
from pyyoutube import Api as YTAPI

yt_token = open(r"yt_api_key.txt").read()
print(yt_token)
yt_api = YTAPI(api_key=yt_token)


YTDL_OPTIONS = {'format': 'bestaudio'}
FFMPEG_OPTIONS = {
'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

servers: dict[str, ServerMusicData] = {}

class MusicCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="test")
    async def play_song(self, ctx: commands.Context, *, args: str = None):
        print(args)

        servers[ctx.guild.id] = ServerMusicData([])

        ytdl = YoutubeDL(YTDL_OPTIONS)
        
        if re.search("^.*(youtu.be\/|list=)([^#\&\?]*).*", args):
            # Play playlist
            playlist_id = args.split("list=")[1].split("&")[0]
            print(playlist_id)

            await ctx.send("Getting links, depending on the size of the playlist this could take a while...")
            playlist_items: list[PlaylistItem] = yt_api.get_playlist_items(playlist_id=playlist_id).items
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
            video_info: video.Video = yt_api.get_video_by_id(video_id=video_id).items[0]
            #print(video_info)
        
            song = Song(video_info.snippet.title.strip(), video_info.snippet.description, video_info.snippet.channelTitle, video_info.snippet.thumbnails.default.url, args, (video_info.contentDetails.duration))
            servers[ctx.guild.id].add_song(song)

        else:
            await ctx.send("Invalid URL.")
            return
            # TODO: implement search

        channel = ctx.author.voice.channel
        
        vc = await channel.connect()
        await play_queue(ctx, vc, ctx.guild.id, FFMPEG_OPTIONS, YTDL_OPTIONS)

def get_playback_url(url, ytdlOps):
    print(url)
    try:
        with YoutubeDL(ytdlOps) as y:
            info = y.extract_info(url, download=False)
            return info
    except Exception as e:
        print(e)
        return e

async def play_queue(ctx: commands.Context, vc: VoiceClient, guildID, ffmpegOps, ytdlOps):
    current = servers[guildID].get_current_song()
    vc
    info = get_playback_url(current.url, ytdlOps)
    if isinstance(info, Exception):
        await ctx.send("An error occurred downloading:\n {}".format(current.title))
        servers[guildID].queueIndex += 1
        if servers[guildID].queueIndex >= len(servers[guildID].queue):
            await ctx.send("Finished!")
            await vc.disconnect()
        else:
            await play_queue(ctx, vc, guildID, ffmpegOps, ytdlOps)
        return

    dl_URL = info["url"]
    dur = info["duration"]
    print(dur)

    embed = discord.Embed()
    embed.add_field(name="Now Playing", value="[{0}]({1})".format(current.title, current.url), inline=False)
    embed.add_field(name="Duration", value='%d:%02d' % (dur / 60, dur % 60), inline=False)
    embed.set_thumbnail(url=current.thumbnail)
    embed.colour = 0xFFff00
    await ctx.send(embed=embed)

    vc.play(discord.FFmpegPCMAudio(dl_URL, **ffmpegOps))
    while vc.is_playing():
        await asyncio.sleep(0.5)
    
    servers[guildID].queueIndex += 1
    if servers[guildID].queueIndex >= len(servers[guildID].queue):
        await ctx.send("Finished!")
        await vc.disconnect()
        return

    await play_queue(ctx, vc, guildID, ffmpegOps, ytdlOps)







def setup(client):
    client.add_cog(MusicCommands(client))