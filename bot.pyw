import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import sys

# --- FINAL FFMPEG PATH FIX ---
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")

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
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        actual_ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg.exe"
        
        return cls(discord.FFmpegPCMAudio(filename, executable=actual_ffmpeg, **ffmpeg_options), data=data)

# Buttons for Music Control
class MusicControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸️")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Music Paused", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, emoji="▶️")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Music Resumed", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Music is not paused", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Stopped & Disconnected", ephemeral=True)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".p [song name]"))
    print(f'✅ RAGE MUSIC BOT IS ONLINE')

@bot.command()
async def p(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Voice channel join karo pehle!")

    vc = ctx.voice_client
    if not vc:
        try:
            vc = await ctx.author.voice.channel.connect()
        except Exception as e:
            return await ctx.send(f"Developed By Rehan: {e}")

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(search, loop=bot.loop, stream=True)
            
            if vc.is_playing():
                vc.stop()
            
            vc.play(player)

            # --- EMBED LOGIC ---
            embed = discord.Embed(title="Now Playing", description=f"**[{player.title}]({player.webpage_url})**", color=0x1DB954)
            embed.set_thumbnail(url=player.thumbnail)
            duration = player.duration or 0
            mins, secs = divmod(duration, 60)
            embed.add_field(name="Duration", value=f"{mins:02d}:{secs:02d}", inline=True)
            embed.add_field(name="Requested By", value=ctx.author.mention, inline=True)
            embed.set_footer(text="RAGE MUSIC SYSTEM")

            try:
                await ctx.send(embed=embed, view=MusicControl())
            except Exception:
                await ctx.send(f"🎶 **Now Playing:** {player.title}")

        except Exception as e:
            if "ffmpeg" in str(e).lower():
                await ctx.send(f"❌ FFmpeg Error. Path being used: `{FFMPEG_PATH}`")
            else:
                await ctx.send(f"❌ Error: {e}")

# Bot Token
bot.run('MTQ5ODIzMzQzMzYyNzk1NTI0Mg.GiSknD.KNwD28PgOtYRSjvCfRiMfMstfsHUXDWj7Bx9Fs')