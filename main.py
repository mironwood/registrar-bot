import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import psycopg2
import re

load_dotenv()
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

def sanitize_channel_name(name):
    name = name.lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9\-]", "", name)

# Database setup
def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def setup_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS invite_roles (invite_code TEXT PRIMARY KEY, role_id BIGINT);")
            conn.commit()

def save_invite_mapping(code, role_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO invite_roles (invite_code, role_id) VALUES (%s, %s) ON CONFLICT (invite_code) DO NOTHING;", (code, role_id))
            conn.commit()

def get_role_id_from_code(code):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role_id FROM invite_roles WHERE invite_code = %s;", (code,))
            result = cur.fetchone()
            return result[0] if result else None

@bot.event
async def on_ready():
    await tree.sync()
    setup_database()
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print('📡 Slash commands synced.')

@tree.command(name="createclass", description="Create a class role, channel, and invite link")
@app_commands.describe(class_name="The name of the class (e.g. Level 2 - Tuesdays 6PM)")
@app_commands.checks.has_permissions(administrator=True)
async def createclass(interaction: discord.Interaction, class_name: str):
    try:
        guild = interaction.guild
        role_name = class_name
        channel_name = sanitize_channel_name(class_name)

        # Create role
        role = await guild.create_role(name=role_name)

        # Find or create the category
        category = discord.utils.get(guild.categories, name="🏗️CLASSES")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)

        # Create invite
        invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)

        save_invite_mapping(invite.code, role.id)

        # Format response
        response = (
            f"We’d love to have you join the Curious Comedy Community Discord server!\n\n"
            f"**If you’re new to the server:**\n"
            f"Click this invite link to join:\n"
            f"🔗 https://discord.gg/{invite.code}\n"
            f"When you join using that link, you’ll automatically be given access to your class’s private channel.\n\n"
            f"**If you’re already a server member:**\n"
            f"1. Open the Discord server.\n"
            f"2. In any text channel, type the following command:\n"
            f"`/joinclass {invite.code}`\n"
            f"This will manually give you access to your class’s private channel.\n\n"
            f"Your class is titled **{class_name}** and will appear under the “CLASSES” section of the server.\n\n"
            f"If you run into any issues, reach out to your instructor or one of the server moderators. We’re glad you’re here!"
        )

        await interaction.response.send_message(response, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        print(f"Error in /createclass: {e}")

@tree.command(name="joinclass", description="Join your class using your code")
@app_commands.describe(code="The code your instructor sent you")
async def joinclass(interaction: discord.Interaction, code: str):
    role_id = get_role_id_from_code(code)
    if role_id:
        role = interaction.guild.get_role(role_id)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"You've been added to **{role.name}**!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Role not found.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ That code wasn't found. Please check the email from your instructor.", ephemeral=True)

@bot.event
async def on_member_join(member):
    pass  # Invite tracking not used currently

bot.run(TOKEN)
