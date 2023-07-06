from ast import alias
import discord
from discord.ext import commands
 
from yt_dlp import YoutubeDL
 
import json
 
 
class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
        # all the music related stuff
        self.is_playing = False
        self.is_paused = False
        self.current = ""
 
        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {
            'format': 'm4a/bestaudio/best',
            'noplaylist': 'True',
            'dump_single_json': 'True',
            'extract_flat': 'True'
        }
 
        self.FFMPEG_OPTIONS = {
            'before_options':
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
 
        self.vc = None
 
    # searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item,
                                        download=False)['entries'][0]
            except Exception:
                return False
        info = ydl.sanitize_info(info)
        url = info['formats'][0]['url']
        title = info['title']
        return {
            'title': title,
            'source': url
        }
 
    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
 
            # get the first url
            m_url = self.music_queue[0][0]['source']
 
            # remove the first element as you are currently playing it
            self.music_queue.pop(0)
 
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after=lambda e: self.play_next())
        else:
            self.is_playing = False
 
    # infinite loop checking
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
 
            m_url = self.music_queue[0][0]['source']
 
            # try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()
 
                # in case we fail to connect
                if self.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
 
            # remove the first element as you are currently playing it
            self.music_queue.pop(0)
 
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after=lambda e: self.play_next())
        else:
            self.is_playing = False
 
    @commands.command(name="play",
                      aliases=["p", "playing"],
                      help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
 
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.send("Connect to a voice channel!")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            self.current = song
            if type(song) == type(True):
                await ctx.send(
                    "Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format."
                )
            else:
                await ctx.send("Song added to the queue")
                self.music_queue.append([song, voice_channel])
 
                if not self.is_playing:
                    await self.play_music(ctx)
                    self.is_playing = True
 
    @commands.command(name="pause",
                      help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
 
    @commands.command(name="resume",
                      aliases=["r"],
                      help="Resumes playing with the discord bot")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.vc.resume()
            self.is_playing = True
            self.is_paused = False
 
    @commands.command(name="skip",
                      aliases=["s"],
                      help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            # try to play next in the queue if it exists
            await self.play_music(ctx)
 
    @commands.command(name="queue",
                      aliases=["q"],
                      help="Displays the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            # display a max of 5 songs in the current queue
            if (i > 4): break
            retval += self.music_queue[i][0]['title'] + "\n"
 
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")
 
    @commands.command(name="clear",
                      aliases=["c", "bin"],
                      help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")
 
    @commands.command(name="leave",
                      aliases=["disconnect", "l", "d"],
                      help="Kick the bot from VC")
    async def dc(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
 
    @commands.command(name="current",
                      aliases=["now"],
                      help="Displays the current song")
    async def current(self, ctx):
        retval = "Now Playing: " + self.current['title']
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

bot.run('#Bot token removed, as it can be stolen(replace it with urs)')