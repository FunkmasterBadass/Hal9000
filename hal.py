import os
import json
import requests
import datetime as dt
from random import randint
from fuzzywuzzy import process
import discord
from discord.ext import commands
from discord.embeds import Embed

bot = commands.Bot(command_prefix='!')

@bot.command()
async def flip(ctx):
    """ flips a coin """
    if randint(0,1) == 1:
        await ctx.send(file=discord.File('Heads.png'))
    else:
        await ctx.send(file=discord.File('Tails.png'))

@bot.command()
async def roll(ctx, *dice_str: str):
    """Rolls a dice in NdN format."""
    result = ''
    for dice in dice_str:
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.send('Format has to be in NdN!')
            return
        for r in range(rolls):
            num = randint(1, limit)
            if limit == 10:
                num = (num - 1) * 10
                num = '00' if num == 0 else f'{num}'
            result = f'{result}, {num}' if result else f'{num}'
    await ctx.send(f"{ctx.author.mention} rolled {result}!")

@bot.command()
@commands.has_role('Admin')
async def mute_all(ctx, channel: str):
    try:
        for c in ctx.guild.voice_channels:
            if channel.lower() == c.name.lower():
                for member in c.members:
                    await member.edit(mute=True)
    except Exception as e:
        print(e)
    await ctx.send(f"muted all members in server {channel}")

@bot.command()
@commands.has_role('Admin')
async def unmute_all(ctx, channel: str):
    try:
        for c in ctx.guild.voice_channels:
            if channel.lower() == c.name.lower():
                for member in c.members:
                    await member.edit(mute=False)
    except Exception as e:
        print(e)
    await ctx.send(f"unmuted all members in server {channel}")

@bot.command()
@commands.has_role('Admin')
async def mute(ctx, mention: str):
    try:
        for member in ctx.guild.members:
            if f'{member.id}' in mention:
                await member.edit(mute=True)
    except Exception as e:
        print(e)
    await ctx.send(f"muted {mention}")

@bot.command()
@commands.has_role('Admin')
async def unmute(ctx, mention: str):
    try:
        for member in ctx.guild.members:
            if f'{member.id}' in mention:
                await member.edit(mute=False)
    except Exception as e:
        print(e)
    await ctx.send(f"muted {mention}")

@bot.group()
async def dota(ctx):
    """
    Dota related functions
    """
    if ctx.invoked_subcommand is None:
        await ctx.send('Command supports the following:\n`!dota lastGame`\nRemember to set `!dota steamid` first')

@dota.command()
async def steamid(ctx, steamid: int):
    """
    Sets the steamid for the dota api usage
    to get your steamid use https://steamidfinder.com
    steamID3: [U:1:80614277] 
    and it's 80614277
    """
    if os.path.exists(f'{ctx.author.id}'):
        with open(f'{ctx.author.id}', 'r') as f:
            user_dict = json.load(f)
        user_dict['steamid'] = steamid
    else:
        user_dict = {'steamid': steamid}
    with open(f'{ctx.author.id}', 'w') as f:
        json.dump(user_dict, f)
    await ctx.send(f"set ID: {steamid} for {ctx.author.mention}")

@dota.command()
async def lastGame(ctx):
    """
    Fetches latest game stats
    """
    if os.path.exists(f'{ctx.author.id}'):
        with open(f'{ctx.author.id}', 'r') as f:
            user_dict = json.load(f)
        steamid = user_dict.get('steamid', False)
    else:
        await ctx.send('No steamid configured, did you run `!dota steamid <steam32ID>` ?')
        return
    if steamid is False:
        await ctx.send('No steamid configured, did you run `!dota steamid <steam32ID>` ?')
        return
    r = requests.get(f'https://api.opendota.com/api/players/{steamid}/recentMatches')
    if r.status_code != 200:
        e_msg = "Either I hit the rate limit or your steamid wasn't correct."
        e_msg = f"{e_msg}\nSteamid should be steam32 account id"
        await ctx.send(e_msg)
        return
    try:
        data = json.loads(r.text)[0]
    except:
        e_msg = "malformed or empty response!"
        await ctx.send(e_msg)
        return
    embed = Embed(title="Last Match", url=f"https://www.dotabuff.com/matches/{data['match_id']}", color=0xffd200)
    embed.set_thumbnail(url="https://www.dotabuff.com/assets/dotabuff-opengraph-b17d3bd0ba45b284eb2760acaaf394433560a220fcea9391a5eaa487be5823e1.png")
    embed.add_field(name='duration', value=f"{data['duration']//60}m {data['duration']%60}s")
    for field,key in [
        ('hero damage', 'hero_damage'),
        ('hero healing', 'hero_healing'),
        ('tower damage', 'tower_damage'),
        ('last hits', 'last_hits'),
        ('gpm', 'gold_per_min'),
        ('xpm', 'xp_per_min'),
    ]:
        embed.add_field(name=field, value=data[key])
    embed.add_field(name='k/d/a', value=f"{data['kills']}/{data['deaths']}/{data['assists']}")
    await ctx.send(f"https://www.dotabuff.com/matches/{data['match_id']}", embed=embed)

@bot.group()
async def terraria(ctx):
    """
    terraria related functions
    """
    if ctx.invoked_subcommand is None:
        await ctx.send('Command supports the following:\n`!terraria recipe <item>')

@terraria.command()
async def recipe(ctx, *item_name: str):
    """
    terraria recipes
    """
    with open('terraria_data.plist', 'r') as f:
        terraria_data= json.loads(f.read())
    item_name = " ".join(item_name).strip()
    items = terraria_data['items']
    recipes = terraria_data['recipes']
    found_recipes = []
    found_item = {}
    name, confidence = process.extractOne(item_name, [item.get('name', '') for item in items])
    if confidence < 90:
        await ctx.send(f"Couldn't find close match, did you mean {name}?\nConfidence: {confidence}")
        return

    for item in items:
        if item.get('name', '') == name:
            found_item = item
            break
    for recipe in found_item.get('recipes', []):
        found_recipes.append(recipes[recipe])
    
    message = ''
    for idx,recipe in enumerate(found_recipes):
        message = f"{message}Recipe {idx+1}:\n"
        crafting_stations = ''
        for station in recipe.get('stations', []):
            crafting_stations = f"{crafting_stations}{items[station].get('name', '')}\n"
        ingredients = ''
        for ing in recipe.get('ingredients', []):
            amount = ing['amount']
            item = ing['item']
            ingredients = f"{ingredients}{amount} {items[item].get('name', '')}\n"
        message = f"{message}{crafting_stations}{ingredients}"
    if message == '':
        await ctx.send(f"No recipe found for {name}.")
    await ctx.send(message)


bot.run('token')