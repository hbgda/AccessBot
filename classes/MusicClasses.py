


from discord.voice_client import VoiceClient


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
    volume = 1
    queueIndex = 0
    guildID = 0
    vc: VoiceClient

    def __init__(self, guildID,queue = []):
        self.queue = queue
        self.guildID = guildID


    def add_song(self, song: Song):
        self.queue.append(song)

    def remove_song(self, song: Song):
        self.queue.remove(song)

    def set_volume(self, volume):
        self.volume = volume

    def set_queue(self, queue: list[Song]):
        self.queue = queue
        self.queueIndex = 0

    def get_current_song(self) -> Song:
        return self.get_song_at_index(self.queueIndex)

    def get_song_at_index(self, index) -> Song | None:
        if index >= len(self.queue):
            return None
        return self.queue[index]

    def clear_queue(self):
        self.queue.clear()
    

