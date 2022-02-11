import discord
import asyncio
import math

from discord.ext import commands
from discord.voice_client import VoiceClient
from helper_functions import format_str, get_playback_info

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
        try:
            index = self.queue.index(song)
        except:
            return
        
        if index <= self.queueIndex:
            self.queueIndex -= 1
        
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
        try:
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
            embed.add_field(name="Now Playing", value="[{0}]({1})".format(format_str(current.title), current.url), inline=False)
            embed.add_field(name="Duration", value='%d:%02d' % (playback_duration / 60, playback_duration % 60), inline=False)
            embed.set_thumbnail(url=current.thumbnail)
            embed.colour = 0x4a54e7

            _next = self.serverMusicData.get_next_song()
            if _next:
                embed.add_field(name="Next Up", value="[{0}]({1})".format(format_str(_next.title), _next.url), inline=False)

            await self.context.send(embed=embed)

            self.vc.play(discord.FFmpegPCMAudio(playback_url, **FFMPEG_OPTIONS))
            self.vc.source = discord.PCMVolumeTransformer(self.vc.source, self.volume)

            # Maybe fixes a bug where it'll sometimes rarely skip a song?
            # (assuming the bug is caused by both vc.is_playing() and vc.is_paused() being false while it is downloading the initial audio data)
            # (could be entirely wrong idk)
            # THIS SHIT IS DRIVING ME INSANE I HAVE NO FUCKING CLUE WHATS CAUSING IT TO RANDOMLY SKIP A SONG IT DOESNT ERROR WHAT THE FUCK

            while self.vc.is_playing() == False:
                await asyncio.sleep(.4)

            while self.vc.is_playing() or self.vc.is_paused():
                if self.is_playing == False:
                    return
                await asyncio.sleep(.1)

            await self.play_next()
        except Exception as e:
            print(e)   

    async def play_next(self):
        self.is_playing = False
        await asyncio.sleep(.5)
        if self.serverMusicData.get_next_song():
            self.serverMusicData.queueIndex += 1
            self.vc.stop()
            await self.play_queue()
        else:
            await self.context.send("Finished!")
            self.serverMusicData.queue.clear()
            self.serverMusicData.queueIndex = 0
            await self.vc.disconnect()
    
    async def play_prev(self):
        self.is_playing = False
        await asyncio.sleep(.3)
        if self.serverMusicData.get_prev_song():
            self.serverMusicData.queueIndex -= 1
            self.vc.stop()
            await self.play_queue()
        else:
            await self.context.send("No previous songs.")
            #await self.vc.disconnect()
    
    def pause(self):
        self.vc.pause()

    def resume(self):
        self.vc.resume()
        
    def set_volume(self, vol):
        self.volume = vol
        self.vc.source.volume = vol

    def get_queue_embed(self, page = 1, amount = 5):
        embed = discord.Embed(title="Queue")
        
        songs = self.serverMusicData.queue

        if page < 1:
            page = 1
        elif page > math.ceil(len(songs)/amount):
            page = math.ceil(len(songs)/amount)

        start_index = (page - 1) * amount
        end_index = min(page * amount, len(songs))
        while start_index < end_index:
            s = songs[start_index]
            if self.serverMusicData.get_current_song() == s:
                embed.add_field(name=str(start_index + 1) + " (Playing)", value="[{0}]({1})".format(format_str(s.title + " - {0}".format(s.uploader), 60), s.url), inline=False)
            else:
                embed.add_field(name=start_index + 1, value="[{0}]({1})".format(format_str(s.title + " - {0}".format(s.uploader), 60), s.url), inline=False)
            start_index += 1

        embed.colour = 0x4a54e7
        embed.set_footer(text="Page {0}/{1}".format(page, math.ceil(len(songs)/amount)))

        return embed