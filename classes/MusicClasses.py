import discord
import asyncio

from discord.ext import commands
from discord.voice_client import VoiceClient
from helper_functions import get_playback_info

FFMPEG_OPTIONS = {
'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Song():
    title: str = ""
    description: str = ""
    uploader: str = ""
    thumbnail: str = ""
    url: str = ""
    duration: float = 0

    def __init__(self, title, description, uploader, thumbnail, url, duration):
        self.title = title
        self.description = description
        self.uploader = uploader
        self.thumbnail = thumbnail
        self.url = url
        self.duration = duration


class ServerMusicData():

    queue: list[Song] = []
    queueIndex = 0

    def __init__(self, guildID,queue = []):
        self.queue = queue
        self.guildID = guildID


    def add_song(self, song: Song):
        self.queue.append(song)

    def remove_song(self, song: Song):
        self.queue.remove(song)

    def set_queue(self, queue: list[Song]):
        self.queue = queue
        self.queueIndex = 0

    def get_next_song(self) -> Song | None:
        return self.get_song_at_index(self.queueIndex + 1)

    def get_prev_song(self) -> Song | None:
        return self.get_song_at_index(self.queueIndex - 1)

    def get_current_song(self) -> Song:
        return self.get_song_at_index(self.queueIndex)

    def get_song_at_index(self, index) -> Song | None:
        if index >= len(self.queue) or index < 0:
            return None
        return self.queue[index]

    def clear_queue(self):
        self.queue.clear()
    

class ServerMusicPlayer():

    serverMusicData: ServerMusicData
    vc: VoiceClient
    ytdl_ops: dict
    context: commands.Context
    volume = 1
    is_playing = True


    def __init__(self, ctx: commands.Context ,vc: VoiceClient = None, serverMusicData: ServerMusicData = None, ytdl_ops = {'format': 'bestaudio'}):
        self.serverMusicData = serverMusicData
        self.vc = vc
        self.ytdl_ops = ytdl_ops
        self.context = ctx

    async def play_queue(self):
        self.is_playing = True

        current = self.serverMusicData.get_current_song()
        
        info = get_playback_info(current.url, self.ytdl_ops)
        if isinstance(info, Exception):
            await self.context.send("Error playing:\n`{0}`".format(current.title))
            self.play_next()
            return

        playback_url = info["url"]
        playback_duration = info["duration"]

        embed = discord.Embed()
        embed.add_field(name="Now Playing", value="[{0}]({1})".format(current.title, current.url), inline=False)
        embed.add_field(name="Duration", value='%d:%02d' % (playback_duration / 60, playback_duration % 60), inline=False)
        embed.set_thumbnail(url=current.thumbnail)
        embed.colour = 0x4a54e7

        _next = self.serverMusicData.get_next_song()
        if _next:
            embed.add_field(name="Next Up", value="[{0}]({1})".format(_next.title, _next.url), inline=False)

        await self.context.send(embed=embed)

        self.vc.play(discord.FFmpegPCMAudio(playback_url, **FFMPEG_OPTIONS))
        self.vc.source = discord.PCMVolumeTransformer(self.vc.source, self.volume)

        while self.vc.is_playing() or self.vc.is_paused():
            if self.is_playing == False:
                return
            await asyncio.sleep(.2)
        
        await self.play_next()   

    async def play_next(self):
        self.is_playing = False
        await asyncio.sleep(.3)
        if self.serverMusicData.get_next_song():
            self.serverMusicData.queueIndex += 1
            self.vc.stop()
            await self.play_queue()
        else:
            await self.context.send("Finished!")
            await self.vc.disconnect()
    
    async def play_prev(self):
        self.is_playing = False
        await asyncio.sleep(.3)
        if self.serverMusicData.get_prev_song():
            self.serverMusicData -= 1
            await self.vc.stop()
            await self.play_queue()
        else:
            await self.context.send("No previous songs.")
            #await self.vc.disconnect()
    
    def pause(self):
        self.vc.pause()
        return

    def resume(self):
        self.vc.resume()
        return

    def set_volume(self, vol):
        self.volume = vol
        self.vc.source.volume = vol
        return