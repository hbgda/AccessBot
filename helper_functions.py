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


def format_str(string, length = 34):
    if len(string) > length:
        return string[0:length] + "..."
    return string