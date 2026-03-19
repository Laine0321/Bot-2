import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import os
from datetime import datetime
import pytz

# --- CONFIGURATION ---
GOV_GREEN = 0x0D7F43
LOGO_URL = "https://media.discordapp.net/attachments/1296716507803291661/1483961280694976752/ManitobaGovLogo.png?ex=69bc7e23&is=69bb2ca3&hm=bdaf874707c014d72cd45a390203d02ca3138bcf25db83740900cfd3c06b513d"
TIMEZONE = pytz.timezone('Canada/Central')

# ROLE IDS
PERMITTED_ROLES = [1481395679380246558, 1481395710745251870]
PING_TARGET_ROLE = 1484021253340925992
# Added the new bypass ID to this list
COOLDOWN_BYPASS_ROLES = [1481394167971188887, 1481394073485971488]

# --- UTILITIES ---

def get_gov_timestamp():
    now = datetime.now(TIMEZONE)
    return f"Manitoba Government - {now.strftime('%I:%M %p')} CST"

def create_gov_embed(title, description=None):
    embed = discord.Embed(title=title, description=description, color=GOV_GREEN)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text=get_gov_timestamp())
    return embed

def has_business_access(interaction: discord.Interaction) -> bool:
    return any(role.id in PERMITTED_ROLES for role in interaction.user.roles)

def business_cooldown_check(interaction: discord.Interaction):
    """Checks multiple roles for cooldown bypass."""
    if any(role.id in COOLDOWN_BYPASS_ROLES for role in interaction.user.roles):
        return None  # No cooldown applied
    return app_commands.Cooldown(1, 3600)  # 1 hour cooldown for others

# --- UI COMPONENTS ---

class StatusModal(Modal, title="Update Government Bot Status"):
    status_text = TextInput(label="Status Message", placeholder="e.g., Serving Manitobans", required=True, max_length=100)
    async def on_submit(self, interaction: discord.Interaction):
        await bot.change_presence(activity=discord.CustomActivity(name=self.status_text.value))
        await interaction.response.send_message(embed=create_gov_embed("✅ Status Updated", f"Set to: **{self.status_text.value}**"), ephemeral=True)

class DashView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Update Status", style=discord.ButtonStyle.primary, emoji="📢")
    async def set_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StatusModal())
    @discord.ui.button(label="Sync Commands", style=discord.ButtonStyle.success, emoji="🔄")
    async def sync_cmds(self, interaction: discord.Interaction, button: discord.ui.Button):
        await bot.tree.sync()
        await interaction.response.send_message("✅ Commands Synced.", ephemeral=True)

# --- BOT CLASS ---

class ManitobaGovBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ {self.user} is online.")

bot = ManitobaGovBot()

# --- SLASH COMMANDS ---

@bot.tree.command(name="businessping", description="Ping the business role (1hr cooldown).")
@app_commands.checks.dynamic_cooldown(business_cooldown_check)
async def businessping(interaction: discord.Interaction):
    if not has_business_access(interaction):
        return await interaction.response.send_message("❌ You do not have the required business roles to use this.", ephemeral=True)

    await interaction.response.send_message("I've sent your business ping!", ephemeral=True)

    content = (
        f"<@&{PING_TARGET_ROLE}>\n"
        f"-# This ping was sent by {interaction.user.mention}"
    )
    await interaction.channel.send(content=content)

@bot.tree.command(name="govdash", description="Government Developer Dashboard.")
@app_commands.checks.has_permissions(administrator=True)
async def govdash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_gov_embed("🏛️ Manitoba Government Dashboard"), view=DashView())

@bot.tree.command(name="ping", description="Check connection speed.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_gov_embed("📡 Connection Status", f"Latency is `{round(bot.latency * 1000)}ms`"))

# --- PREFIX COMMAND FOR SYNCING ---
@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Slash commands synced.")

# --- ERROR HANDLING ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        minutes = round(error.retry_after / 60)
        await interaction.response.send_message(f"⏳ **Cooldown active.** You can use this again in {minutes} minutes.", ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Admin permissions required.", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
