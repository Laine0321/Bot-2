import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import os
from datetime import datetime
import pytz

# --- CONFIGURATION ---
GOV_GREEN = 0x0D7F43
LOGO_URL = "https://media.discordapp.net/attachments/1296716507803291661/1483961280694976752/ManitobaGovLogo.png?ex=69bc7e23&is=69bb2ca3&hm=bdaf874707c014d72cd45a390203d02ca3138bcf25db83740900cfd3c06b513d&=&format=webp&quality=lossless&width=264&height=264"
TIMEZONE = pytz.timezone('Canada/Central')

# --- UTILITIES ---

def get_gov_timestamp():
    now = datetime.now(TIMEZONE)
    return f"Manitoba Government - {now.strftime('%I:%M %p')} CST"

def create_gov_embed(title, description=None):
    embed = discord.Embed(title=title, description=description, color=GOV_GREEN)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text=get_gov_timestamp())
    return embed

# --- UI COMPONENTS ---

class StatusModal(Modal, title="Update Government Bot Status"):
    status_text = TextInput(
        label="Status Message", 
        placeholder="e.g., Serving Manitobans", 
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await bot.change_presence(activity=discord.CustomActivity(name=self.status_text.value))
        embed = create_gov_embed("✅ Status Updated", f"The bot status has been set to: **{self.status_text.value}**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class SyncConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm Global Sync", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await bot.tree.sync()
            await interaction.followup.send(f"✅ Success! `{len(synced)}` slash commands synced globally.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Sync Error: `{e}`", ephemeral=True)

class DashView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Update Status", style=discord.ButtonStyle.primary, emoji="📢")
    async def set_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StatusModal())

    @discord.ui.button(label="Sync Commands", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def sync_cmds(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_gov_embed("⚠️ Command Sync Confirmation", "This will refresh all slash commands globally. It may take a few minutes to update for all users.")
        await interaction.response.send_message(embed=embed, view=SyncConfirmView(), ephemeral=True)

# --- BOT CLASS ---

class ManitobaGovBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        # Initialize with a prefix just for the sync command
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ {self.user} is now online and slash commands are ready.")
        await self.change_presence(activity=discord.CustomActivity(name="Serving Manitoba"))

bot = ManitobaGovBot()

# --- SLASH COMMANDS ---

@bot.tree.command(name="govdash", description="Access the Government Developer Dashboard.")
@app_commands.checks.has_permissions(administrator=True)
async def govdash(interaction: discord.Interaction):
    embed = create_gov_embed("🏛️ Manitoba Government Dashboard")
    embed.add_field(name="📡 System Latency", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    embed.add_field(name="🟢 Status", value="`Online / Active`", inline=True)
    
    await interaction.response.send_message(embed=embed, view=DashView())

@bot.tree.command(name="ping", description="Check connection speed.")
async def ping(interaction: discord.Interaction):
    embed = create_gov_embed("📡 Connection Status", f"Latency is `{round(bot.latency * 1000)}ms`")
    await interaction.response.send_message(embed=embed)

# --- PREFIX COMMAND FOR SYNCING ---

@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    """Run !sync to register slash commands the first time."""
    await bot.tree.sync()
    await ctx.send("✅ Slash commands have been synced globally.")

# --- ERROR HANDLING ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        embed = create_gov_embed("❌ Access Denied", "Required government credentials (Admin) are missing.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        print(f"Error: {error}")

bot.run(os.getenv('DISCORD_TOKEN'))
