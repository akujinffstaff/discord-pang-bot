import discord
from discord.ext import commands
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp
import os

# ============================================================
# CONFIGURATION
# ============================================================

PREFIX = "!"
WELCOME_CHANNEL_NAME = "welcome"

# Direct raw URL for your GitHub repository image
BACKGROUND_URL = "https://raw.githubusercontent.com/akujinffstaff/discord-assets/main/WelcomeUserTemplate.png"

# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ============================================================
# BOT SETUP
# ============================================================

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

warnings = {}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_font(size, bold=True):
    # Select font file based on weight
    font_filename = "arlrdbd.ttf" if bold else "arial.ttf"
    font_path = os.path.join("fonts", font_filename)

    try:
        return ImageFont.truetype(font_path, size)
    except Exception as error:
        print(f"Failed to load font '{font_path}': {error}")
        return ImageFont.load_default()

def shorten(text, length):
    if len(text) <= length:
        return text
    return text[:length - 3] + "..."

# ============================================================
# CREATE WELCOME CARD (GITHUB IMAGE LINK)
# ============================================================

async def create_welcome_card(member):
    WIDTH = 1200
    HEIGHT = 500

    # Download Background Image from GitHub
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BACKGROUND_URL) as response:
                if response.status == 200:
                    bg_bytes = await response.read()
                    bg_image = Image.open(BytesIO(bg_bytes)).convert("RGBA")
                    bg_image = bg_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
                else:
                    raise Exception(f"HTTP Status {response.status}")
    except Exception as error:
        print(f"Background image load error: {error}")
        bg_image = Image.new("RGBA", (WIDTH, HEIGHT), (18, 20, 28, 255))

    # Translucent Center Panel
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    panel_left = 300
    panel_top = 175
    panel_right = 900
    panel_bottom = 465
    
    overlay_draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=20,
        fill=(15, 18, 25, 140)
    )

    image = Image.alpha_composite(bg_image, overlay)
    draw = ImageDraw.Draw(image)

    # Fonts
    welcome_font = get_font(38, bold=True)
    username_font = get_font(34, bold=True)
    details_font = get_font(26, bold=True)
    small_font = get_font(18, bold=False)

    # Circular Avatar
    avatar_x = 515
    avatar_y = 230
    avatar_size = 170
    GOLD_BORDER = (212, 137, 43)

    try:
        avatar_bytes = await member.display_avatar.read()
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        border_thickness = 5
        draw.ellipse(
            (
                avatar_x - border_thickness,
                avatar_y - border_thickness,
                avatar_x + avatar_size + border_thickness,
                avatar_y + avatar_size + border_thickness
            ),
            fill=GOLD_BORDER
        )

        image.paste(avatar, (avatar_x, avatar_y), mask)
    except Exception as error:
        print(f"Avatar processing error: {error}")

    # Text Rendering (Center Aligned)
    ORANGE_COLOR = (235, 138, 38)
    WHITE_COLOR = (255, 255, 255)

    draw.text((WIDTH / 2, 200), f"Welcome to {member.guild.name}!", font=welcome_font, fill=WHITE_COLOR, anchor="mm")
    draw.text((WIDTH / 2, 418), f"User: {shorten(member.display_name, 20)}", font=username_font, fill=ORANGE_COLOR, anchor="mm")
    draw.text((WIDTH / 2, 448), f"Member Count: {member.guild.member_count:,}", font=details_font, fill=WHITE_COLOR, anchor="mm")
    draw.text((WIDTH / 2, 475), f"Welcome to {member.guild.name} — Where Forever Begins.", font=small_font, fill=(220, 220, 220), anchor="mm")

    output = BytesIO()
    image.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output

# ============================================================
# BOT EVENTS & COMMANDS
# ============================================================

@bot.event
async def on_ready():
    print("=" * 55)
    print(f"Bot online: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 55)
    try:
        await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help"))
    except Exception as error:
        print(f"Presence error: {error}")

@bot.event
async def on_member_join(member):
    channel = discord.utils.find(
        lambda c: c.name.lower() == WELCOME_CHANNEL_NAME.lower(),
        member.guild.text_channels
    )

    if channel is None:
        print(f"#{WELCOME_CHANNEL_NAME} not found in {member.guild.name}")
        return

    try:
        card = await create_welcome_card(member)
        file = discord.File(card, filename="welcome.png")
        await channel.send(content=f"👋 Welcome {member.mention}!", file=file)
        print(f"Welcome message sent for {member}")
    except Exception as error:
        print(f"Welcome card error: {error}")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}! 👋")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Owner", value=f"<@{guild.owner_id}>", inline=True)
    embed.add_field(name="👥 Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="💬 Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="🆔 Server ID", value=str(guild.id), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title="👤 User Information", color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=str(member), inline=True)
    embed.add_field(name="Display Name", value=member.display_name, inline=True)
    embed.add_field(name="ID", value=str(member.id), inline=False)
    if member.joined_at:
        embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, style="F"), inline=False)
    embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, style="F"), inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if amount < 1 or amount > 100:
        await ctx.send("❌ Amount must be between 1 and 100.")
        return
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        message = await ctx.send(f"🧹 Deleted **{len(deleted) - 1}** messages.")
        await message.delete(delay=3)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if member == ctx.author or member == ctx.guild.owner:
        await ctx.send("❌ Cannot kick this user.")
        return
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 **{member}** was kicked.\nReason: `{reason}`")
    except discord.Forbidden:
        await ctx.send("❌ Insufficient permissions.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if member == ctx.author or member == ctx.guild.owner:
        await ctx.send("❌ Cannot ban this user.")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 **{member}** was banned.\nReason: `{reason}`")
    except discord.Forbidden:
        await ctx.send("❌ Insufficient permissions.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int = 10, *, reason="No reason provided"):
    try:
        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await member.timeout(until, reason=reason)
        await ctx.send(f"⏰ **{member}** timed out for **{minutes} minutes**.")
    except discord.Forbidden:
        await ctx.send("❌ Insufficient permissions.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"✅ Removed timeout from **{member}**.")
    except discord.Forbidden:
        await ctx.send("❌ Insufficient permissions.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    key = (ctx.guild.id, member.id)
    warnings.setdefault(key, []).append(reason)
    await ctx.send(f"⚠️ **{member}** warned. Reason: `{reason}`. Total: **{len(warnings[key])}**")

@bot.command()
async def warnings_list(ctx, member: discord.Member = None):
    member = member or ctx.author
    key = (ctx.guild.id, member.id)
    user_warnings = warnings.get(key, [])
    if not user_warnings:
        await ctx.send(f"✅ **{member}** has no warnings.")
        return
    text = "\n".join(f"**{i}.** {reason}" for i, reason in enumerate(user_warnings, 1))
    embed = discord.Embed(title=f"⚠️ Warnings — {member}", description=text, color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🤖 Commands", color=discord.Color.blue())
    embed.add_field(name="🔧 General", value="`!hello` `!ping` `!serverinfo` `!userinfo`", inline=False)
    embed.add_field(name="🛡️ Moderation", value="`!clear` `!kick` `!ban` `!timeout` `!untimeout` `!warn` `!warnings_list`", inline=False)
    await ctx.send(embed=embed)

# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable is missing.")
    else:
        bot.run(TOKEN)
