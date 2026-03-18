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
        activity = discord.CustomActivity(name=self.status_text.value)
        await bot.change_presence(activity=activity)
        await interaction.response.send_message(f"✅ Status updated to: **{self.status_text.value}**", ephemeral=True)

class SyncConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm Global Sync", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await bot.tree.sync()
            await interaction.followup.send(f"✅ Success! `{len(synced)}` commands synced globally.", ephemeral=True)
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
        embed = create_gov_embed("⚠️ Command Sync Confirmation", "This will refresh all slash commands globally across Discord. Proceed?")
        await interaction.response.send_message(embed=embed, view=SyncConfirmView(), ephemeral=True)

# --- BOT CLASS ---

class ManitobaGovBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ {self.user} is now online for Manitoba Government.")
        await self.change_presence(activity=discord.CustomActivity(name="Serving Manitoba"))

bot = ManitobaGovBot()

# --- COMMANDS ---

@bot.hybrid_command(name="govdash", description="Access the Government Developer Dashboard.")
@commands.has_permissions(administrator=True)
async def govdash(ctx):
    embed = create_gov_embed("🏛️ Manitoba Government Dashboard")
    embed.add_field(name="📡 System Latency", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    embed.add_field(name="🟢 Status", value="`Online / Active`", inline=True)
    
    await ctx.reply(embed=embed, view=DashView())

@bot.hybrid_command(name="ping", description="Check connection speed.")
async def ping(ctx):
    embed = create_gov_embed("📡 Connection Status", f"Latency is `{round(bot.latency * 1000)}ms`")
    await ctx.reply(embed=embed)

# --- ERROR HANDLING ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = create_gov_embed("❌ Access Denied", "You do not have the required government credentials (Admin) to use this.")
        await ctx.reply(embed=embed, ephemeral=True)

# Railway uses environment variables for security
bot.run(os.getenv('DISCORD_TOKEN'))
