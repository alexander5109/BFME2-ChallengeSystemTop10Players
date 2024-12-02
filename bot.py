import mytoken
import discord
from discord.ext import commands
import asyncio
import logging
import aiohttp
from flask import Flask
from threading import Thread
from functools import wraps, cached_property
from icecream import ic
from enum import Enum
from datetime import datetime
import random
import json
import requests
import cha as cha_module


##-------------------------------------------------------------------##
##------------------------class.Setup.class--------------------------##
##-------------------------------------------------------------------##
app = Flask('')
@app.route('/')
def home():
	return "Hello. I am alive!"

def run_app():
	app.run(host='0.0.0.0',port=8080)

def keep_alive():
	Thread(target=run_app).start()
	
intents = discord.Intents.default()
intents.message_content = True
prefix = "!"
bot = commands.Bot(command_prefix=prefix, intents=intents)

logging.basicConfig(level=logging.INFO)

    

##-------------------------------------------------------------------##
##------------------------class.Enums.class--------------------------##
##-------------------------------------------------------------------##
class WebhooksURL(Enum):
	THEPIG = "https://discord.com/api/webhooks/840359006945935400/4Ss0lC1i2NVNyZlBlxfPhDcdjXCn2HqH-b2oxMqGmysqeIdjL7afF501gLelNXAe0TOA"
	
	
class DiscordID(Enum):
    TEMPT = "573249577801482270"
    ECTH = "280848366030815233"
    LAU = "247181526574432257"

class ChannelID(Enum):
	TOP10_STATUS = 751191825938776096
	MESS_HALL = 826409834819616808
	TOP_SECRET = 715315610870874192
	ADMIN = 801338722515157012


    
##-------------------------------------------------------------------##
##------------------------class.RandonMap.class------------------##
##-------------------------------------------------------------------##
class RandomMatchGenerator:
	@staticmethod
	def string_random_match(player1="bumbi", player2="undy"):
		bfme2factions = ["Men", "Elves", "Dwarves", "Isengard", "Mordor", "Goblins"]
		result = f"""	{random.sample(bfme2factions, k=2)}
			{player1} vs {player2}
			{random.choice(bfme2maps_1v1)}
		"""
		return result
    
##-------------------------------------------------------------------##
##------------------------class.QuotesManager.class------------------##
##-------------------------------------------------------------------##
class QuotesManager:
	def __init__(self, json_quotes):
		self.json_quotes = json_quotes
		with open(self.json_quotes, "r", encoding="utf-8") as file:
			self.quotes = [ Quote( AUTHORS[quo_json["author"]], Quote.Type[quo_json["type"]], quo_json["year"],quo_json["content"] ) for quo_json in json.load(file)]

	##-----------Public----------------##
	def serialize_quotes(self):
		quotes_data = [quote.json() for quote in self.quotes]
		with open(self.json_quotes, "w", encoding="utf-8") as file:
			json.dump(quotes_data, file, indent=4, ensure_ascii=False)
			
	def get_daily_quote(self):
		today_int = datetime.now().weekday()
		return {
			0: self.lunes_quotes,
			1: self.martes_quotes,
			2: self.miercoles_quotes,
			3: self.jueves_quotes,
			4: self.viernes_quotes,
			5: self.sabado_quotes,
			6: self.sunday_quotes,
		}[today_int]().format_as_daily()
	
	def get_random_quote_from(self, author=None, year=None, type=None, format=True):
		filtered_quotes = self.quotes
		if author is not None:
			filtered_quotes = [quote for quote in filtered_quotes if quote.author == author]
		if year is not None:
			filtered_quotes = [quote for quote in filtered_quotes if quote.year == year]
		if type is not None:
			filtered_quotes = [quote for quote in filtered_quotes if quote.type == type]
		if not filtered_quotes:
			raise ValueError("No quotes match the given criteria.")
		quote = random.choice(filtered_quotes)
		return quote.format_as_quote() if format else quote
			
	##-----------------SemiPublic----------------##
	def lunes_quotes(self):
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.TRUCKY, format=False),
			QUOTES.get_random_quote_from(AUTHORS.SHINODA, format=False),
			QUOTES.get_random_quote_from(AUTHORS.MUSTAFA, format=False),
			QUOTES.get_random_quote_from(AUTHORS.TEMPTATION, type=Quote.Type.CCC, format=False),
		])
	def martes_quotes(self):
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.PICABOO, format=False),
			QUOTES.get_random_quote_from(AUTHORS.SILVERBANE, format=False),
			QUOTES.get_random_quote_from(AUTHORS.GRENDAL, format=False),
			QUOTES.get_random_quote_from(AUTHORS.BEYONCE, format=False),
		])
	def miercoles_quotes(self):
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.DARYL, format=False),
			QUOTES.get_random_quote_from(AUTHORS.PANDORUM, format=False),
			QUOTES.get_random_quote_from(AUTHORS.IMPERIALIST, format=False),
			QUOTES.get_random_quote_from(AUTHORS.XELENOS, format=False),
		])
	def jueves_quotes(self):
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.GUERRILLA, format=False),
			QUOTES.get_random_quote_from(AUTHORS.SAVAGE, format=False),
			QUOTES.get_random_quote_from(AUTHORS.THORIN, format=False),
		])
		
	def viernes_quotes(self):
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.CLEVER, format=False),
			QUOTES.get_random_quote_from(AUTHORS.MAYSHADOW, format=False),
			QUOTES.get_random_quote_from(AUTHORS.ANDYBRANDY, format=False),
			QUOTES.get_random_quote_from(AUTHORS.MAKA, format=False),
			QUOTES.get_random_quote_from(AUTHORS.UGANDA_SIMON, format=False),
			QUOTES.get_random_quote_from(AUTHORS.UGANDA_PASTA, format=False),
			QUOTES.get_random_quote_from(AUTHORS.UGANDA_PEPE, format=False),
		])
		
	def sabado_quotes(self):
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.SAURON, format=False),
			QUOTES.get_random_quote_from(AUTHORS.SERTAÇ, format=False),
			QUOTES.get_random_quote_from(AUTHORS.OTTO, format=False),
		])
		
	def sunday_quotes(self): ##sunday
		return random.choice([
			QUOTES.get_random_quote_from(AUTHORS.LAZAR, format=False),
			QUOTES.get_random_quote_from(AUTHORS.LAU, format=False),
			QUOTES.get_random_quote_from(AUTHORS.SHANKS, format=False),
			QUOTES.get_random_quote_from(AUTHORS.ECTH, format=False),
			QUOTES.get_random_quote_from(AUTHORS.TAKEOVER, format=False),
		])


##-------------------------------------------------------------------##
##--------------------------class.Quote.class------------------------##
##-------------------------------------------------------------------##
class Quote:
	class Type(Enum):
		QUOTE = "**%sQuote of %s**"
		AUTISM = "**%sAutism of %s**"
		G_WORD = "**%sWord of %s**"
		CHAT = "**%sChat of %s**"
		RAVE = "**%sRave of %s**"
		RANT = "**%sRant of %s**"
		BALANCE = "**%sBalance request of %s:**"
		CCC = "**%sCreative collective concatenation of %s:**"
		
	def __init__(self, author, type, year, content):
		self.author = author
		self.type = type
		self.year = year
		self.content = content
		
	##-----------------Public----------------##
	def format_as_quote(self):
		return (
			self.type.value %("", self.author.value)
			+ (f"\n**Year: {self.year}**" if self.year else "")
			+ self.__clean_content(self.content)
		)
		
	def format_as_daily(self):
		todays = f"{datetime.now().strftime('%A')}'s "
		return (
			self.type.value %(todays, self.author.value)
			+ (f"\n**Year: {self.year}**" if self.year else "")
			+ self.__clean_content(self.content)
		)
		
	def json(self):
		return {
			"author": self.author.name,
			"type": self.type.name,
			"year": self.year,
			"content": self.__fully_clean_content(self.content),
		}
		
	##-----------------Private----------------##
	def __clean_content(self, quote):
		quote = quote if "\n" in quote else f"\t\t{quote}"
		quote = quote if not quote.startswith("\n") else quote.replace("\n","",1)
		return "\n\t\t" + quote.replace("\n","\n\t\t") 
		
	def __fully_clean_content(self, quote):
		return quote.strip().replace("\t","")
		
		
		

##-------------------------async.Begins-----------------------------##
@bot.event
async def on_ready():
	print("Everything's all ready to go~")
	hourIntegrer = int(datetime.now().strftime("%H"))
	# if hourIntegrer in {4, 12, 20}:
	if hourIntegrer in {4, 12, 20, 15}:
		await bot.get_channel(ChannelID.MESS_HALL.value).send(QUOTES.get_daily_quote())

@bot.command()
async def clear(ctx, N = 2):
	if str(ctx.author.id) in [DiscordID.TEMPT.value, DiscordID.LAU.value, DiscordID.ECTH.value]:
		await ctx.channel.purge(limit = N + 1)

@bot.command()
async def kick(ctx, member: discord.Member, *, reason = None):
	if str(ctx.author.id) in [DiscordID.TEMPT.value, DiscordID.LAU.value, DiscordID.ECTH.value]:
		await member.kick(reason = reason)

@bot.command()
async def top(channel):
	await channel.send(f"See current Top 10 best player list here: <#{ChannelID.TOP10_STATUS.value}>")

@bot.command()
async def random_match(channel):
	await channel.send(string_random_match())

@bot.command()
async def echo(ctx, *, content:str):
	await ctx.send(content)


@bot.command()
async def channel(ctx, *, content:str):
	await ctx.send(ctx.channel.name)


##-------------------------GetFromAuthor-----------------------------##
@bot.command()	
async def today(channel):
	await channel.send(QUOTES.get_daily_quote())

@bot.command()
async def grek(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.OTTO) )


@bot.command()
async def simon(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.UGANDA_SIMON) )

@bot.command()
async def pasta(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.UGANDA_PASTA) )

@bot.command()
async def pepe(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.UGANDA_PEPE) )


@bot.command()
async def low(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.LAU) )


@bot.command()
async def gorilla(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.GUERRILLA) )


@bot.command()
async def mype(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.MUSTAFA) )

@bot.command()
async def blance(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.MUSTAFA, type=Quote.Type.BALANCE) )


@bot.command()
async def sulver(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.SILVERBANE) )


@bot.command()
async def geylenos(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.XELENOS) )


@bot.command()
async def puca(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.PICABOO) )


@bot.command()
async def undy(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.ANDYBRANDY) )

@bot.command()
async def muka(channel):
	await channel.send( QUOTES.get_random_quote_from(AUTHORS.MAKA) )

@bot.command()
async def chalog(channel, cha_id):
	if str(channel.author.id) in [DiscordID.ECTH.value]:
		if cha_id.isnumeric():
			cha = cha_module.SISTEMA.CHALLENGES.get(int(cha_id))
			if cha:
				success_status = cha.send_to_chlng_updates(WebhooksURL.THEPIG.value)
			else:
				success_status = f"Challenge Nº {cha_id} not found"
		else:
			success_status = f"Invalid challenge ID: {cha_id}"
		await channel.send(success_status)
	else:
		await channel.send("You don't have permissions to send this shit.")


	


##-------------------------------------------------------------------##
##--------------------------class.Main.class------------------------##
##-------------------------------------------------------------------##
if __name__ == "__main__":
	AUTHORS = Enum("AUTHORS", json.load(open(r"data/authors.json", "r", encoding="utf-8")))
	QUOTES = QuotesManager(r"data\quotes.json", )
	keep_alive()
	bot.run(mytoken.TOKEN)
	