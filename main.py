import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import json

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f"We have logged in as {self.user}.")


client = aclient()
tree = app_commands.CommandTree(client)


@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(
        f"Pong! Latency: {latency}ms", ephemeral=True
    )


@tree.command(name="purge", description="Purge messages")
async def purge(interaction: discord.Interaction, limit: str):
    if limit.lower() == "none":
        limit = None
    else:
        try:
            limit = int(limit)
            if not 1 <= limit <= 100:
                await interaction.response.send_message(
                    "Please provide a number between 1 and 100 for the limit or 'none' to delete all messages.",
                    ephemeral=True,
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "Invalid limit. Please provide a number between 1 and 100 or 'none' to delete all messages.",
                ephemeral=True,
            )
            return
    user = interaction.user
    role_id = 1137466428988063744
    user_has_role = discord.utils.get(user.roles, id=role_id)
    if not user_has_role:
        await interaction.response.send_message(
            "You do not have the necessary role to use this command.", ephemeral=True
        )
        return
    if not interaction.guild.me.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "I don't have the necessary permissions to delete messages.", ephemeral=True
        )
        return
    if limit is None:
        await interaction.channel.purge()
        await interaction.response.send_message(
            "All messages have been purged.", ephemeral=True
        )
    else:
        await interaction.channel.purge(limit=limit)
        await interaction.response.send_message(
            f"{limit} messages have been purged.", ephemeral=True
        )


@tree.command(name="xbox", description="Find user stats of an Xbox user")
async def xbox(interaction: discord.Interaction, username: str):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    url = f"https://xboxgamertag.com/search/{username}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    gamerscore_div = soup.find("div", class_="col-auto profile-detail-item")
    gamerscore_span = gamerscore_div.find("span")
    gamerscore_text = gamerscore_div.get_text(strip=True)
    gamerscore_number = gamerscore_text.replace(
        gamerscore_span.get_text(strip=True), ""
    )

    profile_picture_element = soup.find("img", class_="rounded img-thumbnail")
    relative_profile_picture_url = profile_picture_element["src"]

    modified_profile_picture_url = relative_profile_picture_url.replace(
        "//images.weserv.nl/?url=", "https://external-content.duckduckgo.com/iu/?u="
    )

    profile_title = soup.find("h1").text.strip()

    embed = discord.Embed(
        title=profile_title,
        description=f"Gamerscore ```{gamerscore_number}```",
        color=int(config["embed_color"], 16),
    )

    embed.set_thumbnail(url=modified_profile_picture_url)

    await interaction.response.send_message(embed=embed)


@tree.command(name="tiktok", description="Find user stats of an Tiktok user")
async def tiktok(interaction: discord.Interaction, username: str):
    url = f"https://www.tiktok.com/@{username}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        thumbnail = soup.find("meta", attrs={"property": "og:image"})["content"]
        follower_count = int(
            soup.find("strong", attrs={"data-e2e": "followers-count"}).text
        )
        following_count = int(
            soup.find("strong", attrs={"data-e2e": "following-count"}).text
        )
        likes_count = int(soup.find("strong", attrs={"data-e2e": "likes-count"}).text)
        bio = soup.find("h2", attrs={"data-e2e": "user-bio"}).text.strip()

        embed = discord.Embed(
            title=f"TikTok - {username}", color=int(config["embed_color"], 16)
        )
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="Bio", value=bio, inline=False)
        embed.add_field(name="Followers", value=follower_count, inline=False)
        embed.add_field(name="Following", value=following_count, inline=False)
        embed.add_field(name="Likes", value=likes_count, inline=False)

        await interaction.response.send_message(embed=embed)

    except requests.RequestException:
        await interaction.send("An error occurred while fetching the TikTok data.")
    except (TypeError, KeyError, ValueError):
        await interaction.send(
            "Failed to parse the TikTok data. The URL might be invalid or the data format has changed."
        )


@tree.command(name="user", description="Find user stats of an user")
async def user(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user  # Use interaction.user instead of ctx.author
    embed = discord.Embed(title=f"{user.name}", color=int(config["embed_color"], 16))
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    embed.set_thumbnail(url=avatar_url)
    created_at_unix = int(user.created_at.timestamp())
    joined_at_unix = int(user.joined_at.timestamp())
    embed.add_field(
        name="Dates",
        value=f"Created: <t:{created_at_unix}:F>\nJoined: <t:{joined_at_unix}:F> ",
        inline=False,
    )
    roles = [
        role.mention for role in user.roles if role != interaction.guild.default_role
    ]
    roles_str = ", ".join(roles) if roles else "No roles"
    embed.add_field(name=f"Roles ({len(roles)})", value=roles_str, inline=False)
    join_position = (
        sorted(interaction.guild.members, key=lambda m: m.joined_at).index(user) + 1
    )
    mutual_guilds = sum(1 for member in user.mutual_guilds)
    embed.add_field(
        name="Join position",
        value=f"{join_position}  ∙  {mutual_guilds} mutual servers",
        inline=False,
    )

    await interaction.response.send_message(embed=embed)


with open("config.json", "r") as config_file:
    config = json.load(config_file)
TOKEN = config.get("token")
OWNER_DISCORD_USER_ID = config["owner_id"]
client.run(TOKEN)
