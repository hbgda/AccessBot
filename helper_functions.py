from youtube_dl import YoutubeDL

def download_yt(yt_url, path):
    
    ytdl = YoutubeDL()
    ytdl.download(yt_url)
    return True