# Miscellaneous commands for Beardless Bot

from random import choice, randint

import discord
import requests

diceMsg = "Enter !d[number][+/-][modifier] to roll a [number]-sided die and add or subtract a modifier. For example: !d8+3, or !d100-17, or !d6."

prof = "https://cdn.discordapp.com/avatars/654133911558946837/78c6e18d8febb2339b5513134fa76b94.webp?size=1024"

animalList = "cat", "duck", "fox", "rabbit", "panda", "lizard", "axolotl", "bear", "bird", "koala", "raccoon", "kangaroo"

# Wrapper for discord.Embed that defaults to commonly-used values and is easier to define
def bbEmbed(name, value = "", col = 0xfff994):
	return discord.Embed(title = name, description = value, color = col)

# User lookup helper method. Finds user based on username and/or discriminator (#1234)
# Runs in linear time; worst case, does not find a loosely-matching target, takes O(n) operations
def memSearch(text):
	if text.mentions:
		return text.mentions[0]
	if not (" " in text.content and text.guild):
		return text.author
	term = text.content.split(" ", 1)[1].lower()
	semiMatch = looseMatch = None
	for member in text.guild.members:
		if term == str(member).lower():
			return member
		if term == member.name.lower():
			if not "#" in term:
				return member
			semiMatch = member
		if member.nick and term == member.nick.lower() and not semiMatch:
			looseMatch = member
		if not (semiMatch or looseMatch) and term in member.name.lower():
			looseMatch = member
	return semiMatch if semiMatch else looseMatch

def animal(animalType):
	r = "Invalid Animal!"
	if animalType == "cat":
		# cat API has been throwing 503 errors every other call, likely due to rate limiting
		for i in range(10):
			# the loop is to try to make another request if one pulls a 503.
			r = requests.get("https://aws.random.cat/meow")
			if r.status_code == 200:
				return r.json()["file"]
			print(f"{r.status_code}; {r.reason}; cat; count {i + 1}")
	
	if animalType.startswith("dog"):
		breed = None if (len(animalType) == 4 or not (" " in animalType)) else (animalType.split(" ", 1)[1].replace(" ", ""))
		for i in range(10): # dog API has been throwing 522 errors, not sure why
			if not breed:
				r = requests.get("https://dog.ceo/api/breeds/image/random")
				if r.status_code == 200:
					return r.json()["message"]
			elif breed.startswith("breeds"):
				r = requests.get("https://dog.ceo/api/breeds/list/all")
				if r.status_code == 200:
					return "Dog breeds: " + ", ".join(dog for dog in r.json()["message"]) + "."
			elif breed.isalpha():
				r = requests.get("https://dog.ceo/api/breed/" + breed + "/images/random")
				if r.status_code == 200:
					if not r.json()["message"].startswith("Breed not found"):
						return r.json()["message"]
					return "Breed not found! Do !dog breeds to see all the breeds."
		return "Breed not found! Do !dog breeds to see all the breeds."
	
	if animalType in ("bunny", "rabbit"):
		r = requests.get("https://api.bunnies.io/v2/loop/random/?media=gif")
		if r.status_code == 200:
			return r.json()["media"]["gif"]
	
	if animalType in ("panda", "koala", "bird", "raccoon", "kangaroo", "fox"):
		if animalType == "fox":
			r = requests.get("https://randomfox.ca/floof/")
		else:
			r = requests.get("https://some-random-api.ml/animal/" + animalType)
		if r.status_code == 200:
			return r.json()["image"]
	
	if animalType in ("duck", "lizard", "axolotl"):
		if animalType == "duck":
			r = requests.get("https://random-d.uk/api/quack")
		elif animalType == "lizard":
			r = requests.get("https://nekos.life/api/v2/img/lizard")
		else:
			r = requests.get("https://axoltlapi.herokuapp.com/")
		if r.status_code == 200:
			return r.json()["url"]
	
	if animalType == "bear":
		return f"https://placebear.com/{randint(200, 400)}/{randint(200,400)}"

	raise Exception(r)

def animals():
	emb = bbEmbed("Animal Photo Commands:").add_field(inline = False, name = "!dog",
	value = "Can also do !dog breeds to see breeds you can get pictures of with !dog <breed>")
	for animalName in animalList:
		emb.add_field(name = "!" + animalName, value = "_ _")
	return emb

def define(msg):
	word = msg.split(' ', 1)[1]
	r = requests.get("https://api.dictionaryapi.dev/api/v2/entries/en_US/" + word)
	if r.status_code == 200:
		desc = f"Audio: https:{r.json()[0]['phonetics'][0]['audio']}" if "audio" in r.json()[0]['phonetics'][0] else ""
		emb = bbEmbed(word.upper(), desc)
		i = 0
		for entry in r.json():
			for meaning in entry["meanings"]:
				for definition in meaning["definitions"]:
					i += 1
					emb.add_field(name = f"Definition {i}:", value = definition["definition"])
		return emb
	return bbEmbed("Beardless Bot Definitions", "Invalid word!")

def roll(message):
	# Takes a string of the format !dn+b and rolls one n-sided die with a modifier of b. Modifier is optional.
	command = message.split('!d', 1)[1]
	modifier = -1 if "-" in command else 1
	for side in "4", "6", "8", "100", "10", "12", "20":
		if command.startswith(side):
			if len(command) > len(side) and command[len(side)] in ("+", "-"):
				return randint(1, int(side)) + modifier * int(command[1 + len(side):])
			return randint(1, int(side)) if command == side else None
	return None

def rollReport(text):
	result = str(roll(text.content.lower()))
	report = "Invalid side number. Enter 4, 6, 8, 10, 12, 20, or 100, as well as modifiers. No spaces allowed. Ex: !d4+3"
	if result != "None":
		report = f"You got {result}, {text.author.mention}."
	return bbEmbed("Beardless Bot Dice", report)

def fact():
	with open("resources/facts.txt", "r") as f:
		return choice(f.read().splitlines())

def info(text):
	try:
		target = memSearch(text)
		if target:
			# Discord occasionally reports people with an activity as not having one; if so, go invisible and back online
			emb = (bbEmbed("", target.activity.name if target.activity else "", target.color)
			.set_author(name = str(target), icon_url = target.avatar_url).set_thumbnail(url = target.avatar_url)
			.add_field(name = "Registered for Discord on", value = str(target.created_at)[:-7] + " UTC")
			.add_field(name = "Joined this server on", value = str(target.joined_at)[:-7] + " UTC"))
			if len(target.roles) > 1: # Every user has the "@everyone" role, so check if they have more roles than that
				emb.add_field(name = "Roles", value = ", ".join(role.mention for role in target.roles[:0:-1]), inline = False)
				# Reverse target.roles in order to make them display in decreasing order of power
			return emb
	except:
		pass
	return bbEmbed("Invalid target!", "Please choose a valid target. Valid targets are either a ping or a username.", 0xff0000)

def sparPins():
	sparDesc = ("Do the command !spar <region> <other info>.", "For instance, to find a diamond from US-E to play 2s with, I would do:",
		"**!spar US-E looking for a diamond 2s partner**.", "Valid regions are US-E, US-W, BRZ, EU, JPN, AUS, SEA.",
		"!spar has a 2 hour cooldown.", "Please use the roles channel to give yourself the correct roles.")
	return (bbEmbed("How to use this channel.").add_field(name = "To spar someone from your region:", value = "\n".join(sparDesc), inline = False)
	.add_field(name = "If you don't want to get pings:", inline = False,
	value = "Remove your region role. Otherwise, responding 'no' to calls to spar is annoying and counterproductive, and will earn you a warning."))

def av(text):
	try:
		target = memSearch(text)
		if target:
			return (bbEmbed("", "", target.color).set_image(url = target.avatar_url)
		    .set_author(name = str(target), icon_url = target.avatar_url))
	except Exception as err:
		print(err)
		pass
	return bbEmbed("Invalid target!", "Please choose a valid target. Valid targets are either a ping or a username.", 0xff0000)

def commands(text):
	emb = bbEmbed("Beardless Bot Commands", "!commands to pull up this list")
	commandNum = 15 if not text.guild else 20 if text.author.guild_permissions.manage_messages else 17
	commandList = (("!register", "Registers you with the currency system."),
		("!balance", "Checks your BeardlessBucks balance. You can write !balance <@someone>/<username> to see that person's balance."),
		("!bucks", "Shows you an explanation for how BeardlessBucks work."),
		("!reset", "Resets you to 200 BeardlessBucks."),
		("!fact", "Gives you a random fun fact."),
		("!source", "Shows you the source of most facts used in !fact."),
		("!flip [number]", "Bets a certain amount on flipping a coin. Heads you win, tails you lose. Defaults to 10."),
		("!blackjack [number]", "Starts up a game of blackjack. Once you're in a game, you can use !hit and !stay to play."),
		("!d[number][+/-][modifier]", "Rolls a [number]-sided die and adds or subtracts the modifier. Example: !d8+3, or !d100-17."),
		("!brawl", "Displays Beardless Bot's Brawlhalla-specific commands."),
		("!add", "Gives you a link to add this bot to your server."),
		("!av [user/username]", "Display a user's avatar. Write just !av if you want to see your own avatar."),
		("![animal name]", "Gets a random animal picture. See the list of animals with !animals. Example: !duck"),
		("!define [word]", "Shows you the definition(s) of a word."),
		("!ping", "Checks Beardless Bot's latency."),
		("!buy red/blue/pink/orange", "Takes away 50000 BeardlessBucks from your account and grants you a special color role."),
		("!info [user/username]", "Displays general information about a user. Write just !info to see your own info."),
		("!purge [number]", "Mass-deletes messages"),
		("!mute [target] [duration]", "Mutes someone for an amount of time. Accepts either seconds, minutes, or hours."),
		("!unmute [target]", "Unmutes the target."))
	for commandPair in commandList[:commandNum]:
		emb.add_field(name = commandPair[0], value = commandPair[1])
	return emb

def joinMsg():
	addUrl = "(https://discord.com/api/oauth2/authorize?client_id=654133911558946837&permissions=8&scope=bot)"
	return (bbEmbed("Want to add this bot to your server?", "[Click this link!]" + addUrl)
	.set_thumbnail(url = prof).add_field(name = "If you like Beardless Bot...", inline = False,
	value = "Please leave a review on [top.gg](https://top.gg/bot/654133911558946837)."))

def hints():
	with open("resources/hints.txt", "r") as f:
		hints = f.read().splitlines()
		emb = bbEmbed("Hints for Beardless Bot's Secret Word")
		for i in range(len(hints)):
			emb.add_field(name = str(i + 1), value = hints[i])
		return emb

# The following Markov chain code was originally provided by CSTUY SHIP.
def tweet():
	with open('resources/eggtweets_clean.txt', 'r') as f:
		words = f.read().split()
	chains = {}
	keySize = randint(1, 2)
	for i in range(len(words) - keySize):
		key = ' '.join(words[i : i + keySize])
		if key not in chains:
			chains[key] = []
		chains[key].append(words[i + keySize])
	key = s = choice(list(chains.keys()))
	for i in range(randint(10, 35)):
		word = choice(chains[key])
		s += ' ' + word
		key = ' '.join(key.split()[1:keySize + 1]) + ' ' + word if keySize > 1 else word
	return s[0].title() + s[1:]

def formattedTweet(eggTweet):
	# Removes the last piece of punctuation to create a more realistic tweet
	for i in range(len(eggTweet) - 1, -1, -1):
		if eggTweet[i] in (".", "!", "?"):
			return "\n" + eggTweet[:i]
	return "\n" + eggTweet

def noPerms():
	reasons = " ".join(("Beardless Bot requires permissions in order to do just about anything. Without them, I can't do",
	"much, so I'm leaving. If you add me back to this server, please make sure to leave checked the box that grants me",
	"the Administrator permission.\nIf you have any questions, feel free to contact my creator, Captain No-Beard#7511."))
	return bbEmbed("I need admin perms!", reasons, 0xff0000).set_author(name = "Beardless Bot", icon_url = prof)