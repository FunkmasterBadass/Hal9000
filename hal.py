import os
import json
import requests
import discord
from discord.ext import commands
from discord.embeds import Embed
from random import randint

bot = commands.Bot(command_prefix='!')

@bot.command()
async def flip(ctx):
    """ flips a coin """
    if randint(0,1) == 1:
        await ctx.send(file=discord.File('Heads.png'))
    else:
        await ctx.send(file=discord.File('Tails.png'))

@bot.command()
async def roll(ctx, limit: int):
    """ rolls a random number 1-specified number inclusive """
    await ctx.send(f"{ctx.author.mention} rolled {randint(1, limit)}!")

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


bot.run('token')