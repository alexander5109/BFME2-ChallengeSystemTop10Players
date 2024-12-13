from datetime import datetime, UTC
from pathlib import Path
from icecream import ic
import json
# import py7zr
from functools import cached_property
from bidict import bidict
import requests
import csv
import sys
import time
	
	
	
	
	
	
	
	
# //--------------------------------------------------------------------//
# ;;---------------------ok. funciones.input--------------------------;;
# //--------------------------------------------------------------------//


def get_int(msg, indent=0, show_error=True, min=None, max=None):
	while True:
		ingreso = input(f"{'\t'*indent}{msg}")
		try: 
			num = int(ingreso)
			if (min is None or num >= min) and (max is None or num <= max):
				return num
			else:
				print(f"{'\t'*(indent+1)}Error de ingreso: '{ingreso}' esta fuera del rango {min}-{max}.")
		except ValueError:
			if show_error:
				print(f"{'\t'*(indent+1)}Error de ingreso: '{ingreso}' no es un numero.")

def get_boolean(msg, letra1="Y", letra2="N", indent=0):	
	while True:
		ingreso = input(f"{'\t'*indent}{msg} Ingrese {letra1}/{letra2}: ").upper()
		if ingreso == letra1:
			return True
		elif ingreso == letra2:
			return False
	
    
    
#-------------------------------------------------------------------------------------------------------------#
#"""-------------------------------------------Player.Class.01---------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class Player:
	def __init__(self, key, value, rank):
		self.key = key
		self.rank = rank
		self.names = value["nicknames"]
		# self.discord_id = value["discord_id"]

		self.cha_wins = 0
		self.cha_loses = 0
		self.challenges = []
		self.wins_total = 0
		self.wins1v1_total = 0
		self.wins2v2_total = 0
		
		self.games_played_total = 0
		self.games_played_1v1 = 0
		self.games_played_2v2 = 0
		
		
	###--------------------------Public.Methods-----------------------###
	def set_rank(self, challenge):
		if self.key == challenge.challenger.key:
			self.rank = 10 if challenge.is_kick_add_mode else challenge.defender.rank
			return
		elif self.key == challenge.defender.key:
			self.rank += len(challenge.chasys.PLAYERS) if challenge.is_kick_add_mode else 1
			return
		
		if self.rank > challenge.winner.rank:
			self.rank -= 1
			
		if challenge.is_kick_add_mode and 11 > self.rank > challenge.loser.rank:
			self.rank -= 1
		elif self.rank > challenge.loser.rank:
			self.rank += 1
			
	def set_records(self, challenge):
		if challenge.winner.key == self.key:
			self.cha_wins += 1
			self.wins_total += challenge.winner.wins
			self.wins1v1_total += challenge.winner.wins1v1
			self.wins2v2_total += challenge.winner.wins2v2
		elif challenge.loser.key == self.key:
			self.cha_loses += 1
			self.wins_total += challenge.loser.wins
			self.wins1v1_total += challenge.loser.wins1v1
			self.wins2v2_total += challenge.loser.wins2v2
		else:
			raise Exception("This player didn't even participate")
		
		self.games_played_total += challenge.games_total
		self.games_played_1v1 += challenge.games1v1
		self.games_played_2v2 += challenge.games2v2
		
	def get_1v1_vs(self, other, print_em=True):
		self_wins = {cha for cha in self.challenges if cha.winner.history == self and cha.loser.history == other}
		other_wins = {cha for cha in self.challenges if cha.winner.history == other and cha.loser.history == self}
		self_wins_len = len(self_wins)
		other_wins_len = len(other_wins)
		total_matches_len = self_wins_len + other_wins_len
		if total_matches_len == 0:
			winrate = 0
		else:
			winrate = (self_wins_len / total_matches_len) * 100.0
		if print_em:
			print(f"{self.name} vs {other.name}: {self_wins_len}-{other_wins_len} | WinRate: {winrate}")
		else:
			if total_matches_len > 0:
				return self_wins_len > other_wins_len 
			else:
				return None
		
	###--------------------------Public.Properties-----------------------###
	@classmethod
	def instance_with_rank(cls, key, value, legacy):
		if rank:= legacy.inverse.get(key):
			return cls(key, value, rank)
		else:
			rank = len(legacy)+1
			legacy[rank] = key
			return cls(key, value, rank)

	@cached_property
	def name(self):
		return self.names[0]

	@cached_property
	def loses_total(self):
		return self.games_played_total - self.wins_total
		
	@cached_property	
	def loses_1v1_total(self):
		return self.games_played_1v1 - self.wins1v1_total
		
	@cached_property	
	def loses2v2_total(self):
		return self.games_played_2v2 - self.wins2v2_total
	
	@cached_property
	def fecha_de_alta(self):
		return self.challenges[0]

	###--------------------------Public.dundermethod-----------------------###
	def __lt__(self, other):
		return self.key < other.key
		
	def __gt__(self, other):
		def get_cha_winrate(player):
			return (player.wins1v1_total / player.games_played_total) * 100.0 if player.games_played_total != 0 else 0
			
		bol = self.get_1v1_vs(other, print_em=False)
		if bol is None:
			bol = get_cha_winrate(self)  > get_cha_winrate(other)
		print(f"{self.key} better than {other.key} = {bol}")
		return bol

	def __repr__(self):
		return f"|{self.key}|\tRank:{self.rank}\t|Wins:{self.cha_wins}|Loses:{self.cha_loses}"










#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------ChallengeEvent.Class.02----------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class ChallengeEvent:
	def __init__(self, chasys, key, row):
		self.chasys = chasys
		self.key = key
		self.row = row
		self.version = row["version"]
		self.date = datetime.strptime(row["date"], '%Y-%m-%d')
		self.dateString = datetime.strptime(row["date"], '%Y-%m-%d').strftime('%Y-%m-%d')
		self.notes = row['notes']
		self.player1 = PlayerInChallenge(self, row["p1"], row["p1wins1v1"], row["p1wins2v2"])
		self.player2 = PlayerInChallenge(self, row["p2"], row["p2wins1v1"], row["p2wins2v2"])
		
		self.__01_asegurar_row_integrity()
		self.__02_set_player_records()
		self.__03_set_player_ranks()
		self.__04_freeze_current_top_10_string()

	
	###--------------------------Public.Methods-----------------------###
	def post(self, confirmed=False):
		if not confirmed and not get_boolean(f"\tConfirm send challenge Nº{self.key} to Chlng|Updates?"):
			return
		discord_message = "📢 **Challenge Update!** A new match result is in! Check out the details below."
		if self.is_normal_mode:
			response = self.__post_normal_mode(discord_message)
		elif self.is_no_score_mode:
			response = self.__post_no_score_mode(discord_message)
		elif self.is_kick_add_mode:
			response = self.__post_kick_add_mode(discord_message)
		
		if response.status_code in {200, 204}:
			print(f"Challenge Nº{self.key} successfully sent to Discord via the webhook!")
		else:
			print(f"Failed to send webhookof challenge Nº{self.key}: \n{response.status_code} - {response.text}")
		
	###--------------------------Private.Methods-----------------------###
	def __01_asegurar_row_integrity(self):
		if not self.is_normal_mode and self.games_total:
			raise Exception(f"Error en el csv. Los jugadores deben tener 0 wins en un challenge tipo {self.version}.")
		
	def __02_set_player_records(self):
		if self.is_normal_mode:
			self.winner.history.set_records(self)
			self.loser.history.set_records(self)
			
	def __03_set_player_ranks(self):
		if self.challenger is self.winner:
			for player in self.chasys.PLAYERS.values():
				player.set_rank(self)	
			
	def __04_freeze_current_top_10_string(self):
		self.top10 = "\t\tTOP 10\n"
		lista = [player for player in self.chasys.PLAYERS.values() if 1 <= player.rank <= 10]
		for player in sorted(lista, key=lambda p: p.rank, reverse=True):
			self.top10 += f"\t{player.rank:<4}. {player.name:20} {player.cha_wins}-{player.cha_loses}\n"
			
	def __report_01_02_chamessage(self):
		string = (
			f"\n\n{self.challenger.history.name} ({self.challenger.rank_ordinal}) has challenged "
			f"{self.defender.history.name} ({self.defender.rank_ordinal}) for his spot."
		)
		if self.games2v2:
			string += "\nMode: Traditional challenge (4 games as 2vs2, 4 games as 1vs1, untie with 1vs1)."
		return string
		
	def __report_01_report_score(self):
		string = f"\nScore 1vs1: {self.winner.wins1v1}-{self.loser.wins1v1} for {self.winner.history.name}"
		if self.games2v2:
			string += (f"\nScore 2vs2: {self.winner.wins2v2}-{self.loser.wins2v2} for {self.winner.history.name}"
				f"\nScore: {self.winner.wins}-{self.loser.wins} for {self.winner.history.name}"
			)
		return string

	def __report_01_report_defenseortakeover(self):
		flawlessly = "flawlessly " if self.loser.wins == 0 else ""
		if self.defender is self.winner:
			return f"\n\n+ {self.defender.history.name} has {flawlessly}defended the {self.defender.rank_ordinal} spot!"
		else:
			return f"\n\n+ {self.challenger.history.name} has {flawlessly}taken over the {self.defender.rank_ordinal} spot!"

	def __post_no_score_mode(self, discord_message):
		embed = self.embed | {
			"fields": [{
					"name": "Players",
					"value": (
						f"- Challenger: **{self.challenger.history.name} ({self.challenger.rank_ordinal})**"
						f"\n- Defender: **{self.defender.history.name} ({self.defender.rank_ordinal})**"
					),
					"inline": False
				},{
					"name": "Outcome",
					"value": (
						f"- **{self.defender.history.name}** has refused to defend his spot or hasn't arranged a play-date to defend it.\n"
						"```diff\n"
						f"+ {self.challenger.history.name} has taken over the {self.defender.rank_ordinal} spot!\n"
						"```"
					),
					"inline": False
				},{
					"name": "Scores",
					"value": "- No wins or losses have been scored.",
					"inline": False
				},{
					"name": "Let the Challenges Continue!",
					"value": f"```diff\n{self.top10}```",
					"inline": False
				}],
		}
		if self.notes:
			embed["fields"].insert(-2,{
				"name": "Comments: ",
				"value": f"*- {self.notes}*",
				"inline": False
			})
		payload = {
			"content": discord_message,
			"embeds": [embed]
		}
		return requests.post(self.chasys.webhook_url, json=payload)
		
	def __post_kick_add_mode(self, discord_message):
		embed = self.embed | {
			"fields": [{
					"name": "Kick-Add Update",
					"value": (
						f"- Since Challenge {self.defender.previous_challenge.key}, {self.defender.history.name} has not played any game or challenge in {self.defender.days_since_last_chall} days."
					),
					"inline": False
				},{
					"name": "Outcome",
					"value": (
						"```diff\n"
						f"- {self.defender.history.name} ({self.defender.rank_ordinal}) has been kicked from the list.\n"
						f"+ {self.challenger.history.name} has been set to in the 10th spot.\n"
						"```"
					),
					"inline": False
				},{
					"name": "Scores",
					"value": "- No wins or losses have been scored.",
					"inline": False
				},{
					"name": "Let the Challenges Continue!",
					"value": f"```diff\n{self.top10}```",
					"inline": False
				}
			],
		}
		if self.notes:
			embed["fields"].insert(-2,{
				"name": "Comments: ",
				"value": f"*- {self.notes}*",
				"inline": False
			})
		payload = {
			"content": discord_message,
			"embeds": [embed]
		}
		return requests.post(self.chasys.webhook_url, json=payload)
		
		
	def __post_normal_mode(self, discord_message):
		
		while not self.replays_dir.exists():
			if not get_boolean(f"Replay pack not found: << {self.replays_dir.relative_to(self.replays_dir.parent.parent)} >> \n{self.replays_dir.stem}\n\tDo you want to make sure to rename replays accordingly and try again?"):
				sys.exit("Ok bye")
		response = requests.post(
			self.chasys.webhook_url,
			data={"content": discord_message},
			files={"file": open(self.replays_dir, "rb")}
		)
		if response.status_code != 200:
			return response
			
		score = f"- **Score 1vs1**: {self.winner.wins1v1}-{self.loser.wins1v1} for **{self.winner.history.name}**"
		if self.games2v2:
			score += (
				f"\n- **Score 2vs2**: {self.winner.wins2v2}-{self.loser.wins2v2} for **{self.winner.history.name}**"
				f"\n- **Total Score**: {self.winner.wins}-{self.loser.wins} for **{self.winner.history.name}**"
			)
		embed = self.embed | {
			"fields": [{
					"name": "Players",
					"value": (
						f"- Challenger: **{self.challenger.history.name} ({self.challenger.rank_ordinal})**"
						f"\n- Defender: **{self.defender.history.name} ({self.defender.rank_ordinal})**"
					),
					"inline": False
				},{
					"name": "Scores",
					"value": score,
					"inline": False
				},{
					"name": "Outcome",
					"value": (
						"```diff\n"
						f"+ {self.winner.history.name} {'flawlessly ' if self.loser.wins == 0 else ''}{'defended' if self.defender is self.winner else 'has taken over'} the {self.defender.rank_ordinal} spot!\n"
						"```"
					),
					"inline": False
				},{
					"name": "Games Played In",
					"value": f"{self.version}",
					"inline": True
				},{
					"name": "Let the Challenges Continue!",
					"value": f"```diff\n{self.top10}```",
					"inline": False
				}
			],
		}
		if self.notes:
			embed["fields"].insert(-2,{
				"name": "Comments: ",
				"value": f"*- {self.notes}*",
				"inline": False
			})
		webhook_message = response.json()
		message_id = webhook_message["id"]
		webhook_url_edit = f"{self.chasys.webhook_url}/messages/{message_id}"
		edit_payload = {
			"content": discord_message,
			"embeds": [embed]
		}
		return requests.patch(
			webhook_url_edit,
			json=edit_payload
		)

	###--------------------------properties----------------------###
	@cached_property
	def embed(self):
		return {
			"color": 0x5DD9DF if self.is_normal_mode else 0x981D98 if self.is_kick_add_mode else 0xFFA500,
			"title": "A new Challenge has been registered!",
			"description": (
				"```diff\n"
				f"- Challenge № {self.key}\n"
				f"- Update {self.dateString}\n"
				"```"
			),
			"timestamp": datetime.now(UTC).isoformat(),
			"footer": {"text": "Let the challenges continue!"},
		}
	
	@cached_property
	def winner(self):
		return self.player1 if (self.player1.wins > self.player2.wins or not self.is_normal_mode) else self.player2

	@cached_property
	def loser(self):
		return self.player1 if self.winner is self.player2 else self.player2

	@cached_property
	def challenger(self):
		return self.player1 if self.player1.rank > self.player2.rank else self.player2

	@cached_property
	def defender(self):
		return self.player1 if self.challenger is self.player2 else self.player2
		
	@cached_property
	def games_total(self):
		return self.winner.wins + self.loser.wins
		
	@cached_property
	def games1v1(self):
		return self.winner.wins1v1 + self.loser.wins1v1
		
	@cached_property
	def games2v2(self):
		return self.winner.wins2v2 + self.loser.wins2v2
			
	@cached_property
	def is_no_score_mode(self):
		return self.version == "NO_SCORE_MODE"

	@cached_property
	def is_kick_add_mode(self):
		return self.version == "KICK_ADD_MODE"

	@cached_property
	def is_normal_mode(self):
		return not self.is_no_score_mode and not self.is_kick_add_mode
		
	@cached_property
	def replays_dir(self):
		return self.chasys.chareps / f"Challenge{self.key}_{self.challenger.history.key}_vs_{self.defender.history.key},_{self.challenger.wins}-{self.defender.wins},_{self.version}.rar"
			
	###--------------------------Public.dundermethod-----------------------###
	def __lt__(self, other):
		return self.key < other.key
		
	def __repr__(self):
		return f"|Cha{self.key}|{self.version}|{self.winner}{self.winner.wins}|{self.loser}{self.loser.wins}|"
		
	def __str__(self):
		commment_line = f"\n\n\tComment: {self.notes}" if self.notes else ""
		def report_03_kick_add_report():
			return (
				f"\n\nAddAndKickUpdate: "
				f"Since Challenge {self.defender.previous_challenge.key}, {self.defender.history.name} has not played any game or challenge in {self.defender.days_since_last_chall} days."
				f"\n\n- {self.defender.history.name} has been kicked from the {self.defender.rank_ordinal} spot and from the list."
				f"\n\n+ {self.challenger.history.name} has been added to the top10 list, starting in the 10th spot."
				f"{commment_line}"
				f"\n\nNo wins or losses have been scored."
			)
			
		def report_02_no_score_report():
			return (
				f"{self.__report_01_02_chamessage()}"
				f"\n\nSpotUndefended: {self.defender.history.name} has refused to defend his spot or hasn't arranged a play-date to defend it."
				f"\n\n+ {self.challenger.history.name} has taken over the {self.defender.rank_ordinal} spot!"
				f"{commment_line}"
				f"\n\nNo wins or losses have been scored."
			)

		def report_01_normal_report():
			return (
				f"{self.__report_01_02_chamessage()}"
				f"{self.__report_01_report_score()}"
				f"{self.__report_01_report_defenseortakeover()}"
				f"{commment_line}"
				f"\n\nGames were played in {self.version}"
			)
			
		return (
			"\n------------------------------------"
			f"\n{self.replays_dir.stem}"
			"\n```diff\n"
			f"\n- Challenge № {self.key}"
			f"\n- Update {self.dateString}"
			f"{
				report_03_kick_add_report() if self.is_kick_add_mode 
				else report_02_no_score_report() if self.is_no_score_mode 
				else report_01_normal_report()
			}"
			f"\n\nLet the challenges continue!"
			f"\n\n{self.top10}```"
		)





#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------PlayerInChallenge.Class.03--------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class PlayerInChallenge:
	def __init__(self, challenge, key, wins1v1, wins2v2):
		self.key = key
		self.challenge = challenge
		self.wins1v1 = int(wins1v1)
		self.wins2v2 = int(wins2v2)
		self.__01_freeze_current_history()
		self.history.challenges.append(self.challenge)
			
			
			
	###--------------------------Public.Properties-----------------------###
	def __01_freeze_current_history(self):
		self.rank = self.history.rank
		self.wins = self.wins1v1 + self.wins2v2
		
		
		
	@cached_property
	def previous_challenge(self):
		return self.history.challenges[self.history.challenges.index(self.challenge)-1]
		
	@cached_property
	def days_since_last_chall(self):
		return (self.challenge.date - self.previous_challenge.date).days
	
	@cached_property
	def history(self):
		return self.challenge.chasys.PLAYERS[self.key]
		
	@cached_property
	def rank_ordinal(self):
		ordinal = { 1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th", 8: "8th", 9: "9th", 10: "10th"}
		return ordinal.get(self.rank, "from outside the list")
		
	###--------------------------Public.dundermethod-----------------------###
	def __repr__(self):
		return f"|{self.history.key}|"






#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------ChallengeSystem.Class.04-----------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class ChallengeSystem:
	def __init__(self, chareps, chacsv, chalog, status, player_data, webhook_url):
		self.chareps = chareps
		self.chacsv = chacsv
		self.chalog = chalog
		self.status = status
		self.webhook_url = webhook_url
		self.PLAYERS = self.__read_PLAYERS(player_data)
		self.CHALLENGES = self.__read_CHALLENGES()
		
		
	###--------------------------Public.Methods-----------------------###
	def write_csv(self):
		if not get_boolean("Are you sure you want to re-write the .csv database? You better have a backup"):
			return
		data = [cha.row for cha in self.CHALLENGES.values() ]
		if get_boolean("Descendent order?"):
			data.reverse()

		# Write data back to the CSV
		with open(self.chacsv, mode='w', newline='', encoding='latin1') as file:
			if data:
				fieldnames = data[0].keys()
				writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
				writer.writeheader()
				writer.writerows(data)
		print(".csv guardado.")

	def write_status(self):
		super_string = "\n".join(str(player) for player in sorted( self.PLAYERS.values() ))
		with open(self.status, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.status.name} was updated")
			
	def write_chalog(self):
		super_string = f"##AutoGenerated by 'ChallengeSystem' {datetime.today().strftime("%Y-%m-%d")}\nRegards, Bambi\n\n"
		for num, cha in enumerate( sorted( self.CHALLENGES.values(),reverse=True ) , start=1):
			if num == 1:
				ChallengeSystem.rename_folder("torename", cha.replays_dir.stem, compress=False)
				print(cha)
			super_string += str(cha)
		
		with open(self.chalog, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.chalog.name} was updated")
	
	def send_all_posts(self, start_with):
		if not start_with:
			start_with = self.get_challenge().key
		end_with = len(SISTEMA.CHALLENGES)
		if not get_boolean(f"Confirm do you want recursively post challenges between {start_with}-{end_with} each 7 minutes"):
			return
		for chakey in range(start_with, end_with+1):
			self.CHALLENGES[chakey].post(confirmed=True)
			time.sleep(60*7)
			
			
	def __get_validated_argv_dict(self, argv):
		argv_dict = {
			"cha_id": None,
			"post": None,
			"post_all": None
		}
		if len(argv) > 2:
			if argv[1].isnumeric():
				cha_id = int(argv[1])
				min = 1
				max = len(self.CHALLENGES)
				if min <= cha_id <= max:
					argv_dict["cha_id"] = cha_id
				else:
					raise Exception(f"Challenge out of the range {min}-{max} range.")
			else:
				raise Exception(f"Wrong argv: {argv[1]} is not a valid challenge id")
			if argv[2] not in argv_dict:
				raise Exception(f"Wrong argv: {argv[2]} is not a valid method")
			else:
				argv_dict[argv[2]] = True
		return argv_dict	
			
	def execute_argv_operations_if_any(self, argv):
		if len(argv) == 1:
			return
		argv_dict = self.__get_validated_argv_dict(argv)
		if argv_dict["post"]:
			instance = self.CHALLENGES[argv_dict["cha_id"]]
			instance.post(confirmed=True)
		elif argv_dict["post_all"]:
			self.send_all_posts(argv_dict["cha_id"])
			
			
	def get_challenge(self, hint=None):
		min=1
		max=len(self.CHALLENGES)
		if hint is None:
			return self.CHALLENGES[get_int(f"Select challenge. Type the ID (min: {min}, max:{max}): ", indent=0, min=min, max=max)]
		elif result:= self.CHALLENGES.get(hint):
			return result
		else:
			raise Exception(f"Challenge of id {hint} not found. Logged challenges are between {min} and {max}.")

	# def consult_03_player_vs_player(self, p1_key, p2_key, print_em):
		# return self.PLAYERS[p1_key].get_1v1_vs(self.PLAYERS[p2_key], print_em=print_em)
		
	# def consult_04_who_is_black(self, pname):
		# ic(self.PLAYERS[pname].is_black)
	
	# def consult_05_2v2_score(self, pname):
		# ic(self.PLAYERS[pname].wins2v2_total)
		# ic(self.PLAYERS[pname].loses2v2_total)

	
	###--------------------------Private.Methods-----------------------###
	def __read_CHALLENGES(self):
		dataaaa = {}
		if self.chacsv.exists() and self.chacsv.stat().st_size > 0:
			with open(self.chacsv, mode='r', encoding='latin1') as file:
				reader = csv.DictReader(file, delimiter=';')
				rows = sorted(reader, key=lambda row: int(row['key']))
				for row in rows:
					key = int(row['key'])
					dataaaa[key] = ChallengeEvent(self, key, row)
		else:
			raise Exception(f"No existe {self.chacsv}")
		return dataaaa
		
		
	def __read_PLAYERS(self, player_data):
		legacy = bidict({int(key): value for key, value in player_data["legacy"]["top10"].items()})
		if self.chalog.exists():
			return { key: Player.instance_with_rank(key, value, legacy) for key, value in player_data["active"].items() }
		else:
			raise Exception(f"No existe {self.chalog}")
		
		

	###------------------------------Statics-----------------------###
	# @staticmethod
	# def compress_folder(folder_path):
		# if folder_path.exists():
			# if not folder_path.is_dir():
				# raise ValueError("Input path must be a directory.")
			# archive_path = folder_path.with_suffix(".7z")
			# with py7zr.SevenZipFile(archive_path, 'w') as archive:
				# archive.writeall(folder_path)
			# print(f"* {folder_path.name} was 7ziped")


	@staticmethod
	def rename_folder(torename, ideal, compress):
		existing = Path(rf"D:\MEGA\BFME2 - Ecthelion Replays\_ChallengueLeage_Replays\{torename}")
		ideal = Path(rf"D:\MEGA\BFME2 - Ecthelion Replays\_ChallengueLeage_Replays\{ideal}")
		if existing.exists() and not ideal.exists():
			existing.rename(ideal)
			print(f"* {torename} was renamed to {ideal.name}")
		# if compress:
			# ChallengeSystem.compress_folder(ideal)
			
			
		
		
		
		
		
#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------------ok.Iniciar-------------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#

SISTEMA = ChallengeSystem(
	player_data = json.load(open(r"data\players.json")),
	chareps = Path.cwd() / r"replays",
	chacsv = Path.cwd() / r"data\challenges.csv",
	chalog = Path.cwd() / r"output\challenges.log",
	status = Path.cwd() / r"output\status.log",
	webhook_url = "https://discord.com/api/webhooks/840359006945935400/4Ss0lC1i2NVNyZlBlxfPhDcdjXCn2HqH-b2oxMqGmysqeIdjL7afF501gLelNXAe0TOA"
)




	
if __name__ == "__main__":
	SISTEMA.write_chalog();
	SISTEMA.write_status();
	# SISTEMA.write_csv();
	
	
		
	"""1. Consultas functions"""
	# SISTEMA.consult_03_player_vs_player()
	# SISTEMA.consult_04_who_is_black()
	# SISTEMA.consult_05_2v2_score()
	
	"""2. Argv"""
		# python cha.py 312
		# python cha.py 314 post
		# python cha.py 314 post_till_end
	SISTEMA.execute_argv_operations_if_any(sys.argv);
	
	"""3. SendToChlngUpdates"""
	# SISTEMA.get_challenge(hint=None).post()
