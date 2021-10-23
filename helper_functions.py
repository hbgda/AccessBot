from youtube_dl import YoutubeDL

def get_playback_info(url, ytdlOps):
    print(url)
    try:
        with YoutubeDL(ytdlOps) as y:
            info = y.extract_info(url, download=False)
            return info
    except Exception as e:
        print(e)
        return e
