import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import sys
import time

# --- CONFIGURATION ---
STARTUP_CHANNEL_ID = 123456789012345678  # Apne channel ki ID yahan likhein

# --- FFMPEG PATH LOGIC (For Local & Host) ---
# Agar Windows hai toh ffmpeg.exe dhoondega, warna (Render par) direct 'ffmpeg' use karega
if os.name == 'nt': # Windows
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")
else: # Linux/Render
    FFMPEG_PATH = "ffmpeg"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.playing, name="RAGE MUSIC 24/7 🎵")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'✅ {bot.user.name} is Online on Host!')

    channel = bot.get_channel(STARTUP_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="🚀 Host Online", description="Bot is now running on Cloud!", color=0x2ecc71)
        await channel.send(embed=embed)

@bot.command()
async def p(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Voice channel mein aao pehle!")
    
    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(search, loop=bot.loop, stream=True)
            vc.play(player)
            await ctx.send(f"🎶 **Playing:** {player.title}")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

# Yahan apna Token Dalein
bot.run('MTQ5ODIzMzQzMzYyNzk1NTI0Mg.GiSknD.KNwD28PgOtYRSjvCfRiMfMstfsHUXDWj7Bx9Fs')