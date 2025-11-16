"""Beardless Bot methods that modify resources/money.csv."""

import csv
import random
from collections import OrderedDict
from enum import Enum
from operator import itemgetter
from pathlib import Path

import nextcord

from misc import bb_embed, member_search

CommaWarn = (
	"Beardless Bot gambling is available to Discord"
	" users with a comma in their username. Please"
	" remove the comma from your username, {}."
)

NewUserMsg = (
	"You were not registered for BeardlessBucks gambling, so I have"
	" automatically registered you. You now have 300 BeardlessBucks, {}."
)

FinMsg = "Please finish your game of blackjack first, {}."

NoGameMsg = (
	"You do not currently have a game of blackjack"
	" going, {}. Type !blackjack to start one."
)

NoMultiplayerGameMsg = (
	"You do not currently have a multiplayer game of blackjack"
	" going, {}. Type '!blackjack new' to start one."
)

InvalidBetMsg = (
	"Invalid bet. Please choose a number greater than or equal"
	" to 0, or enter \"all\" to bet your whole balance, {}."
)


class BlackjackPlayer:
	def __init__(self, name: nextcord.User | nextcord.Member):
		self.name: nextcord.User | nextcord.Member =  name
		self.hand: list[int] = []
		self.bet: int | str = 10
		self.done: bool = False

	def check_bust(self) -> bool:
		"""
		Check if a user has gone over Goal.

		If so, invert their bet to facilitate subtracting it from their total.

		Returns:
			bool: Whether the user has gone over Goal.

		"""
		if sum(self.hand) > BlackjackGame.Goal:
			self.bet *= -1
			return True
		return False


	def perfect(self) -> bool:
		"""
		Check if the user has reached Goal, and therefore gotten Blackjack.

		In the actual game of Blackjack, getting Blackjack requires hitting
		21 with just your first two cards; for the sake of simplicity, use
		this method for checking if the user has reached Goal at all.

		Returns:
			bool: Whether the user has gotten Blackjack.

		"""
		return sum(self.hand) == BlackjackGame.Goal


class BlackjackGame:
	"""
	Blackjack game instance.

	New instance created for each game. Instances are server-agnostic; only
	one game allowed per player across all servers.

	Attributes:
		AceVal (int): The high value of an Ace
		DealerSoftGoal (int): The soft sum up to which the dealer will hit
		FaceVal (int): The value of a face card (J Q K)
		Goal (int): The desired score
		CardVals (tuple[int, ...]): Blackjack values for each card
		user (nextcord.User or Member): The user who is playing this game
		bet (int): The number of BeardlessBucks the user is betting
		dealerUp (int): The card the dealer is showing face-up
		dealerSum (int): The running count of the dealer's cards
		deck (list): The cards remaining in the deck
		hand (list): The list of cards the user has been dealt
		message (str): The report to be sent in the Discord channel

	Methods:
		check_bust():
			Checks if the user has gone over Goal
		deal_to_player():
			Deals the user a card
		deal_top_card():
			Removes the top card from the deck.
		perfect():
			Checks if the user has reached a Blackjack
		starting_hand():
			Deals the user a starting hand of 2 cards
		stay():
			Determines the game result after ending the game
		card_name(card):
			Gives the human-friendly name of a given card

	"""

	AceVal = 11
	DealerSoftGoal = 17
	FaceVal = 10
	Goal = 21
	CardVals = (2, 3, 4, 5, 6, 7, 8, 9, 10, FaceVal, FaceVal, FaceVal, AceVal)

	def __init__(
		self,
		owner: nextcord.User | nextcord.Member,
		multiplayer: bool,
	) -> None:
		"""
		Create a new BlackjackGame instance.

		In order to simulate the dealer standing on DealerSoftGoal, the
		dealer's sum will be incremented by a random card value until
		reaching DealerSoftGoal.

		Args:
			user (nextcord.User or Member): The user who is playing this game
			bet (int): The number of BeardlessBucks the user is betting

		"""
		self.owner = BlackjackPlayer(owner);
		self.players: list[BlackjackPlayer] = [self.owner]
		self.deck: list[int] = []
		self.deck.extend(BlackjackGame.CardVals * 4)
		self.dealerUp = self.deal_top_card()
		self.dealerSum = self.dealerUp + self.deal_top_card()
		self.multiplayer = multiplayer
		if not multiplayer:
			self.message = self.starting_hand()
		else:
			self.message = "Multiplayer Blackjack game created!\n"

	@staticmethod
	def card_name(card: int) -> str:
		"""
		Return the human-friendly name of a card based on int value.

		Args:
			card (int): The card whose name should be rendered

		Returns:
			str: A human-friendly card name.

		"""
		if card == BlackjackGame.FaceVal:
			return "a " + random.choice(
				(str(BlackjackGame.FaceVal), "Jack", "Queen", "King"),
			)
		if card == BlackjackGame.AceVal:
			return "an Ace"
		return "an 8" if card == 8 else ("a " + str(card))  # noqa: PLR2004

	def deal_top_card(self) -> int:
		"""
		Remove and return the top card from the deck.

		Returns:
			int: The value of the top card of the deck.

		"""
		return self.deck.pop(random.randint(0, len(self.deck) - 1))


	def starting_hand(self) -> str:
		"""
		Deal the user(s) a starting hand of 2 cards.

		Returns:
			str: The message to show the user(s).

		"""
		message: str = (
			f"The dealer is showing {self.dealerUp},"
			" with one card face down. "
		)
		for p in self.players:
			p.hand.append(self.deal_top_card())
			p.hand.append(self.deal_top_card())
			message += (
				f"{p.name.mention} your starting hand consists of"
				f" {BlackjackGame.card_name(p.hand[0])}"
				f" and {BlackjackGame.card_name(p.hand[1])}."
				f" Your total is {sum(p.hand)}. "
			)
			if p.perfect():
				message += (
					f"{p.name.mention} you hit {BlackjackGame.Goal}! You win, {p.name.mention}!"
				)
			else:
				if p.check_bust():
					p.hand[1] = 1
					p.bet *= -1
					message = (
						"Your starting hand consists of two Aces."
						" One of them will act as a 1. Your total is 12. "
					)
				message += (
					"Type !hit to deal another card to yourself, or !stay"
					f" to stop at your current total, {p.name.mention}."
				)
		return message

	def deal_to_player(self, player: BlackjackPlayer) -> str:
		"""
		Deal the user a single card.

		Returns:
			str: The message to show the user.

		"""
		dealt = self.deal_top_card()
		player.hand.append(dealt)
		self.message = (
			f"{player.name.mention} you were dealt {BlackjackGame.card_name(dealt)},"
			f" bringing your total to {sum(player.hand)}. "
		)
		if BlackjackGame.AceVal in player.hand and player.check_bust():
			for i, card in enumerate(player.hand):
				if card == BlackjackGame.AceVal:
					player.hand[i] = 1
					player.bet *= -1
					break
			self.message += (
				"To avoid busting, your Ace will be treated as a 1."
				f" Your new total is {sum(player.hand)}. "
			)
		self.message += (
			"Your card values are {}. The dealer is"
			" showing {}, with one card face down."
		).format(", ".join(str(card) for card in player.hand), self.dealerUp)
		if player.check_bust():
			self.message += f" You busted. Game over, {player.name.mention}."
		elif player.perfect():
			self.message += (
				f" You hit {BlackjackGame.Goal}! You win, {player.name.mention}!"
			)
		else:
			self.message += (
				" Type !hit to deal another card to yourself, or !stay"
				f" to stop at your current total, {player.name.mention}."
			)
		return self.message

	def stay(self, player: BlackjackPlayer) -> bool:
		"""
		Stay the current player.

		if all other players' actions have been exhausted, end the round.

		Returns:
			bool: the round has ended.

		"""
		player.done = True
		for p in self.players:
			if not p.done:
				self.message = (
					f"{player.name.mention} you stayed, "
					"waiting for others to play their turn"
				)
				return False

		# If we got here, then the game has ended.
		while self.dealerSum < BlackjackGame.DealerSoftGoal:
			self.dealerSum += self.deal_top_card()
		self.message = "The dealer has a total of {}. "

		for p in self.players:
			if sum(p.hand) > self.dealerSum and not p.check_bust():
				self.message += f"You're closer to {BlackjackGame.Goal} "
				self.message += (
					"with a sum of {}. You win! Your winnings "
					"have been added to your balance, {}.\n"
				)
			elif sum(p.hand) == self.dealerSum:
				self.message += (
					"That ties your sum of {}. Your bet has been returned, {}.\n"
				)
			elif self.dealerSum > BlackjackGame.Goal:
				self.message += (
					"You have a sum of {}. The dealer busts. You win! "
					"Your winnings have been added to your balance, {}.\n"
				)
			else:
				self.message += f"That's closer to {BlackjackGame.Goal} "
				self.message += (
					"than your sum of {}. You lose. Your loss "
					"has been deducted from your balance, {}.\n"
				)
				p.bet *= -1
			self.message = self.message.format(
				self.dealerSum, sum(p.hand), p.name.mention,
			)
			if not p.bet:
				self.message += (
					"Unfortunately, you bet nothing, so this was all pointless.\n"
				)
		return True


	def get_player(self, player: nextcord.User | nextcord.Member) -> BlackjackPlayer | None:
		for p in self.players:
			if p.name == player:
				return p
		return None


class MoneyFlags(Enum):
	"""Enum for additional readability in the writeMoney method."""

	NotEnoughBucks = -2
	CommaInUsername = -1
	BalanceUnchanged = 0
	BalanceChanged = 1
	Registered = 2


def write_money(
	member: nextcord.User | nextcord.Member,
	amount: str | int,
	*,
	writing: bool,
	adding: bool,
) -> tuple[MoneyFlags, str | int | None]:
	"""
	Check or modify a user's BeardlessBucks balance.

	Args:
		member (nextcord.User or Member): The target user
		amount (str or int): The amount to change member's balance by
		writing (bool): Whether to modify member's balance
		adding (bool): Whether to add to or overwrite member's balance

	Returns:
		tuple[MoneyFlags, str | int | None]: A tuple containing:
			MoneyFlags: enum representing the result of calling the method
			str or int or None: an additional report, if necessary.

	"""
	if "," in member.name:
		return MoneyFlags.CommaInUsername, CommaWarn.format(member.mention)
	with Path("resources/money.csv").open("r", encoding="UTF-8") as csv_file:
		for row in csv.reader(csv_file, delimiter=","):
			if str(member.id) == row[0]:  # found member
				if isinstance(amount, str):  # for people betting all
					amount = -int(row[1]) if amount == "-all" else int(row[1])
				new_bank: str | int = str(
					int(row[1]) + amount if adding else amount,
				)
				if writing and row[1] != new_bank:
					if int(row[1]) + amount < 0:
						return MoneyFlags.NotEnoughBucks, None
					new_line = ",".join((row[0], str(new_bank), str(member)))
					result = MoneyFlags.BalanceChanged
				else:
					# No change in balance. Rewrites lines anyway, to
					# update stringified version of member
					new_line = ",".join((row[0], row[1], str(member)))
					new_bank = int(row[1])
					result = MoneyFlags.BalanceUnchanged
				with Path("resources/money.csv").open(
					"r", encoding="UTF-8",
				) as f:
					money = "".join(list(f)).replace(",".join(row), new_line)
				with Path("resources/money.csv").open(
					"w", encoding="UTF-8",
				) as f:
					f.writelines(money)
				return result, new_bank

	with Path("resources/money.csv").open("a", encoding="UTF-8") as f:
		f.write(f"\r\n{member.id},300,{member}")
	return (
		MoneyFlags.Registered,
		(
			"Successfully registered. You have 300"
			f" BeardlessBucks, {member.mention}."
		),
	)


def register(target: nextcord.User | nextcord.Member) -> nextcord.Embed:
	"""
	Register a new user for BeardlessBucks.

	Args:
		target (nextcord.User or Member): The user to register

	Returns:
		nextcord.Embed: the report of the target's registration.

	"""
	result, bonus = write_money(target, 300, writing=False, adding=False)
	report = bonus if result in {
		MoneyFlags.CommaInUsername, MoneyFlags.Registered,
	} else (
		"You are already in the system! Hooray! You"
		f" have {bonus} BeardlessBucks, {target.mention}."
	)
	assert isinstance(report, str)
	return bb_embed("BeardlessBucks Registration", report)


def balance(
	target: nextcord.User | nextcord.Member | str,
	msg: nextcord.Message,
) -> nextcord.Embed:
	"""
	Check a user's BeardlessBucks balance.

	Args:
		target (nextcord.User or Member or str): The user whose balance is
			to be checked
		msg (nextcord.Message): The message sent that called this command

	Returns:
		nextcord.Embed: the report of the target's balance.

	"""
	report = (
		"Invalid user! Please @ a user when you do !balance"
		" (or enter their username), or do !balance without a"
		f" target to see your own balance, {msg.author.mention}."
	)
	bal_target = (
		member_search(msg, target) if isinstance(target, str) else target
	)
	if bal_target and not isinstance(bal_target, str):
		result, bonus = write_money(
			bal_target, 300, writing=False, adding=False,
		)
		if result == MoneyFlags.BalanceUnchanged:
			report = (
				f"{bal_target.mention}'s balance is {bonus} BeardlessBucks."
			)
		else:
			report = str(bonus) if result in {
				MoneyFlags.CommaInUsername, MoneyFlags.Registered,
			} else "Error!"
	return bb_embed("BeardlessBucks Balance", report)


def reset(target: nextcord.User | nextcord.Member) -> nextcord.Embed:
	"""
	Reset a user's Beardless balance to 200.

	Args:
		target (nextcord.User or Member): The user to reset

	Returns:
		nextcord.Embed: the report of the target's balance reset.

	"""
	result, bonus = write_money(target, 200, writing=True, adding=False)
	report = bonus if result in {
		MoneyFlags.CommaInUsername, MoneyFlags.Registered,
	} else f"You have been reset to 200 BeardlessBucks, {target.mention}."
	assert isinstance(report, str)
	return bb_embed("BeardlessBucks Reset", report)


def leaderboard(
	target: nextcord.User | nextcord.Member | str | None = None,
	msg: nextcord.Message | None = None,
) -> nextcord.Embed:
	"""
	Find the top min(len(money.csv), 10) users by balance in money.csv.

	Runtime = |money.csv| + runtime of sorted(money.csv) + 10
	= O(n) + O(nlog(n)) + 10 = O(nlog(n)).

	Args:
		target (nextcord.User or Member or str or None): The user invoking
			leaderboard() (default is None)
		msg (nextcord.Message or None): the message invoking
			leaderboard(); always present when invoking in server,
			sometimes absent in testing (default is None)

	Returns:
		nextcord.Embed: a summary of the richest users by balance.
			If target is somewhere on the leaderboard, also
			reports target's position and balance.

	"""
	emb = bb_embed("BeardlessBucks Leaderboard")
	if (msg and isinstance(target, str)):
		target = member_search(msg, target)
	if target and isinstance(target, nextcord.User | nextcord.Member):
		write_money(target, 300, writing=False, adding=False)
	with Path("resources/money.csv").open("r", encoding="UTF-8") as csv_file:
		lb_dict = {
			row[2]: int(row[1]) for row in csv.reader(csv_file, delimiter=",")
		}
	# Sort by value for each key in lbDict, which is BeardlessBucks balance
	sorted_dict = OrderedDict(sorted(lb_dict.items(), key=itemgetter(1)))
	pos = target_balance = None
	if target:
		users = list(sorted_dict.keys())
		try:
			pos = len(users) - users.index(str(target))
		except ValueError:
			pos = None
		else:
			target_balance = sorted_dict[str(target)]
	for i in range(min(len(sorted_dict), 10)):
		head, body = sorted_dict.popitem()
		last_entry: bool = (
			i != min(len(sorted_dict), 10) - 1
		)
		emb.add_field(
			name=f"{i + 1}. {head.split("#")[0]}",
			value=str(body),
			inline=last_entry,
		)
	if target and pos:
		assert not isinstance(target, str)
		emb.add_field(name=f"{target.name}'s position:", value=str(pos))
		emb.add_field(
			name=f"{target.name}'s balance:", value=str(target_balance),
		)
	return emb


def flip(author: nextcord.User | nextcord.Member, bet: str | int) -> str:
	"""
	Gamble a certain number of BeardlessBucks on a coin toss.

	Args:
		author (nextcord.User or Member): The user who is gambling
		bet (str): The amount author is wagering

	Returns:
		str: A report of the outcome and how author's balance changed.

	"""
	heads = random.randint(0, 1)
	report = InvalidBetMsg
	if bet == "all":
		if not heads:
			bet = "-all"
	else:
		try:
			bet = int(bet)
		except ValueError:
			bet = -1
	if (
		(isinstance(bet, str) and "all" in bet)
		or (isinstance(bet, int) and bet >= 0)
	):
		result, bank = write_money(author, 300, writing=False, adding=False)
		if result == MoneyFlags.Registered:
			report = NewUserMsg
		elif result == MoneyFlags.CommaInUsername:
			assert isinstance(bank, str)
			report = bank
		elif isinstance(bet, int) and isinstance(bank, int) and bet > bank:
			report = (
				"You do not have enough BeardlessBucks to bet that much, {}!"
			)
		else:
			if isinstance(bet, int) and not heads:
				bet *= -1
			result = write_money(author, bet, writing=True, adding=True)[0]
			report = (
				"Heads! You win! Your winnings have"
				" been added to your balance, {}."
			) if heads else (
				"Tails! You lose! Your losses have been"
				" deducted from your balance, {}."
			)
			if result == MoneyFlags.BalanceUnchanged:
				report += (
					" Or, they would have been, if"
					" you had actually bet anything."
				)
	return report.format(author.mention)

def make_bet(
	author: nextcord.User | nextcord.Member,
	game: BlackjackGame,
	bet: str | int, # expected to be either "all" or a number
) -> tuple[str, int]:
	result, bank = write_money(author, 300, writing=False, adding=False)
	report = ""
	if result == MoneyFlags.Registered:
		report = NewUserMsg
	elif result == MoneyFlags.CommaInUsername:
		assert isinstance(bank, str)
		report = bank
	elif isinstance(bet, int) and isinstance(bank, int) and bet > bank:
		report = (
			"You do not have enough BeardlessBucks to bet that much, {}!"
		)
	elif bet == "all":
		assert bank is not None
		bet = bank
		report = game.message
	return report, int(bet) # this cast should work


def blackjack(
	author: nextcord.User | nextcord.Member, bet: str | int,
) -> tuple[str, BlackjackGame | None]:
	"""
	Gamble a certain number of BeardlessBucks on blackjack.

	Args:
		author (nextcord.User or Member): The user who is gambling
		bet (str): The amount author is wagering

	Returns:
		str: A report of the outcome and how author's balance changed.
		BlackjackGame or None: If there is still a game to play,
			returns the object representing the game of blackjack
			author is playing. Else, None.

	"""
	game = None
	report = InvalidBetMsg
	if bet != "all" and bet != "new":
		try:
			bet = int(bet)
		except ValueError:
			return report.format(author.mention), game
	if (
		(isinstance(bet, str) and bet == "all")
		or (isinstance(bet, int) and bet >= 0)
	):
		game = BlackjackGame(author, multiplayer=False)
		report, bet = make_bet(author, game, bet)
		player = BlackjackPlayer(author)
		player.bet = bet
		if player.perfect():
			write_money(author, bet, writing=True, adding=True)
			game = None
	if isinstance(bet, str) and bet == "new":
		game = BlackjackGame(author, multiplayer=True)
		report = game.message
	return report.format(author.mention), game


def player_in_game(
	games: list[BlackjackGame], author: nextcord.User | nextcord.Member,
) -> tuple[BlackjackGame, BlackjackPlayer] | None:
	"""
	Check if a user has an active game of Blackjack.

	TODO: convert games list to dict[user_id, BlackJackGame], deprecate this.

	Args:
		games (list[BlackjackGame]): list of active Blackjack games
		author (nextcord.User or Member): The user who is gambling

	Returns:
		tuple[BlackjackGame, BlackjackPlayer] or None: The player associated
		with the discord account and the game they're in if they're in one.
		Else, None.

	"""
	for game in games:
		player = game.get_player(author)
		if player is not None:
			return game, player
	return None
