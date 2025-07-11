from datetime import datetime
from pathlib import Path
from icecream import ic
import json
from functools import cached_property
import requests
import sys
import time
# import SECRETS
from dotenv import load_dotenv
from typing import Union, Optional, cast, Any, Callable, Type, List, Dict # type: ignore
import os

# import csv
# from bidict import bidict
# import py7zr
# from abc import ABC, abstractmethod
	
	
load_dotenv()
class SECRETS:
    PIG_WEB_HOOK = os.environ["PIG_WEB_HOOK"]
    TOKEN = os.environ["TOKEN"]
	
	
	
# //--------------------------------------------------------------------//
# ;;---------------------ok. funciones.input--------------------------;;
# //--------------------------------------------------------------------//

		
		
		
def wait_minutes(minutes:int) -> None:
	towait = minutes*60
	print(f"Waiting {towait} minutes...")
	time.sleep(towait)
		

def get_int(msg:str , indent: int=0, show_error: bool=True, min:Optional[int]=None, max:Optional[int]=None) -> int:
	tab = '\t'
	while True:
		if min and max:
			ingreso = input(f"{tab*indent}{msg} (Min:{min},Max:{max}): ")
		elif min:
			ingreso = input(f"{tab*indent}{msg} (Min:{min}): ")
		elif max:
			ingreso = input(f"{tab*indent}{msg} (Max:{max}): ")
		else:
			ingreso = input(f"{tab*indent}{msg}")
		try: 
			num = int(ingreso)
			if (min is None or num >= min) and (max is None or num <= max):
				return num
			else:
				print(f"{tab*(indent+1)}Error de ingreso: '{ingreso}' esta fuera del rango {min}-{max}.")
		except ValueError:
			if show_error:
				print(f"{tab*(indent+1)}Error de ingreso: '{ingreso}' no es un numero.")

def get_boolean(msg:str, letra1:str="Y", letra2:str="N", indent:int=0) -> bool:	
	while True:
		tab = '\t'
		ingreso = input(f"{tab*indent}{msg} Ingrese {letra1}/{letra2}: ").upper()
		if ingreso == letra1:
			return True
		elif ingreso == letra2:
			return False
	
	
	
	
	
	
	
	
	
#-------------------------------------------------------------------------------------------------------------#
#"""-------------------------------------------PlayerHistory.Class.01---------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class PlayerHistory:
	def __init__(self, chasys:"ChallengeSystem", key:str, value:dict[str,list[str]]):
		self.chasys = chasys
		self.key:str = key
		self.names = value["nicknames"]
		# self.discord_id = value["discord_id"]

		self.cha_wins = 0
		self.cha_loses = 0
		self.challenges:list[ChallengeEvent] = []
		self.wins_total = 0
		self.wins1v1_total = 0
		self.wins2v2_total = 0
		
		self.games_played_total = 0
		self.games_played_1v1 = 0
		self.games_played_2v2 = 0
		
		
		
	###----------------PlayerHistory.Public.Methods------------###
	def append_cha(self:"PlayerHistory", challenge:"ChallengeEvent"):
		self.challenges.append(challenge)
		self.games_played_total += challenge.games_total
		self.games_played_1v1 += challenge.games1v1
		self.games_played_2v2 += challenge.games2v2
		
	def append_cha_win_lose(self:"PlayerHistory", player_in_chall:"PlayerInChallenge"):
		self.wins_total += player_in_chall.wins
		self.wins1v1_total += player_in_chall.wins1v1
		self.wins2v2_total += player_in_chall.wins2v2
		if player_in_chall is player_in_chall.challenge.winner:
			self.cha_wins += 1
		else:
			self.cha_loses += 1
	
	def get_status(self):
		return f"|{self.key}|\tRank:{self.get_rank()}\t|Wins:{self.cha_wins}|Loses:{self.cha_loses}"
		
	def get_rank(self):
		return self.chasys.top10list.index(self)
		
	def get_1v1_vs(self:"PlayerHistory", other:"PlayerHistory", print_em:bool=True) -> Optional[bool]:
		self_wins:set[ChallengeEvent] = {cha for cha in self.challenges if cha.winner.history == self and cha.loser.history == other}
		other_wins:set[ChallengeEvent] = {cha for cha in self.challenges if cha.winner.history == other and cha.loser.history == self}
		ic(self_wins)
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
		
	###--------------------PlayerHistory.Public.Properties----------------###
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

	###--------------------PlayerHistory.Dunder.Methods----------------###
	def __lt__(self:"PlayerHistory", other:"PlayerHistory"):
		return self.key < other.key
		
	def __gt__(self:"PlayerHistory", other:"PlayerHistory"):
		def get_cha_winrate(player:"PlayerHistory"):
			return (player.wins1v1_total / player.games_played_total) * 100.0 if player.games_played_total != 0 else 0
			
		bol = self.get_1v1_vs(other, print_em=False)
		if bol is None:
			bol = get_cha_winrate(self)  > get_cha_winrate(other)
		print(f"{self.key} better than {other.key} = {bol}")
		return bol

	def __repr__(self:"PlayerHistory"):
		return f"|{self.key}|\t|Wins:{self.cha_wins}|Loses:{self.cha_loses}"










#------------------------------------------------------------------------------------------#
#"""---------------------------------ChallengeEvent.Class.02----------------------------"""#
#------------------------------------------------------------------------------------------#
# Define an interface
class ChallengeEvent():
	def __init__(self, chasys:"ChallengeSystem", key:int, row:dict[str, str], embed_color:int):
		self.chasys = chasys
		self.key = key
		self.row = row
		self.embed_color = embed_color
		self.version = row["version"]
		self.date = datetime.strptime(row["date"], '%Y-%m-%d')
		self.notes = row['notes']
		self.winner = PlayerInChallenge(self, row["w_key"], row["w_wins1v1"], row["w_wins2v2"])
		self.loser = PlayerInChallenge(self, row["l_key"], row["l_wins1v1"], row["l_wins2v2"])
		self._init_01_integrity_check()
		self._init_02_impact_players_historial()
		self._init_03_impact_system_top10_rank()
		self.top10string = self.__get_top10string()
	
	###--------------------ChallengeEvent.Static.Methods-------------###
	@classmethod
	def new_from_row(cls:Type["ChallengeEvent"], chasys:"ChallengeSystem", key:int, version:str, row_dict:dict[str, str]) -> "ChallengeEvent":
		if version == "NO_SCORE_MODE":
			return NoScoreChallenge(chasys, key, row_dict, embed_color=0xFFA500)  # Orange color for NoScoreChallenge
		elif version == "KICK_ADD_MODE":
			return KickAddChallenge(chasys, key, row_dict, embed_color=0x981D98)  # Purple color for KickAddChallenge
		else:
			return NormalChallenge(chasys, key, row_dict, embed_color=0x5DD9DF)  # Blueish default color for NormalChallenge
					
	
	
	
	###--------------------ChallengeEvent.Public.Methods-------------###
	def preguntar_por_replaypack(self: "ChallengeEvent"):
		if self.replays_dir is None:
			return
		while not self.replays_dir.exists():
			if not get_boolean(f"Replay pack not found: << {self.replays_dir.relative_to(self.replays_dir.parent.parent)} >> \n{self.replays_dir.stem}\n\tDo you want to make sure to rename replays accordingly and try again?"):
				sys.exit("Ok bye")
				
				
	def as_row(self):
		columns = map(lambda x: str(x), [self.key, self.version, self.winner.history.key, self.winner.wins1v1, self.winner.wins2v2, self.loser.history.key, self.loser.wins1v1, self.loser.wins2v2, self.fecha, self.notes])
		return ";".join(columns)+"\n"
		
	def post(self: "ChallengeEvent", confirmed: bool, delay: int):
		if not confirmed and not get_boolean(f"\tConfirm send challenge Nº{self.key} to Chlng|Updates?"):
			return
		self.preguntar_por_replaypack()
		if delay:
			wait_minutes(delay)
		discord_message = "📢 **Challenge Update!** A new match result is in! Check out the details below."
		response = self._06_get_my_post(discord_message)
		
		if response.status_code in {200, 204}:
			print(f"Challenge Nº{self.key} successfully sent to Discord via the webhook!")
		else:
			print(f"Failed to send webhookof challenge Nº{self.key}: \n{response.status_code} - {response.text}")


			
	###--------------------ChallengeEvent.Protected.Methods-------------###
	
	def _init_01_integrity_check(self)-> None:
		"ChallengeEvent - abstract method to be implemented by subclasses"
		raise NotImplementedError("This method should be overridden by subclasses")
	
	def _init_02_impact_players_historial(self) -> None:
		"ChallengeEvent - abstract method to be implemented by subclasses"
		raise NotImplementedError("This method should be overridden by subclasses")
		
	@cached_property
	def embed(self) -> Dict[str, Any]:
		"ChallengeEvent - abstract method to be implemented by subclasses"
		raise NotImplementedError("This method should be overridden by subclasses")
	
	def _init_03_impact_system_top10_rank(self) -> None:
		"ChallengeEvent - winner_takes_over"
		if self.challenger is self.winner:
			self.chasys._apply_a_take_over(self)

	def _04_get_my_report(self) -> str:
		"ChallengeEvent - abstract method to be implemented by subclasses"
		raise NotImplementedError("This method should be overridden by subclasses")
			
	def _05_str_who_challenged_who(self) -> str:
		"ChallengeEvent - Comportamiento normal"
		return (
			f"\n\n{self.challenger.history.name} ({self.challenger.rank_ordinal}) has challenged "
			f"{self.defender.history.name} ({self.defender.rank_ordinal}) for his spot."
		)
	def _06_get_my_post(self, discord_message:str) -> requests.Response:
		"ChallengeEvent - abstract method to be implemented by subclasses"
		raise NotImplementedError("This method should be overridden by subclasses")
		
	def _07_rename_existing_replaypack(self, torename:str, compress:bool) -> None:
		"ChallengeEvent - abstract method to be implemented by subclasses"
		raise NotImplementedError("This method should be overridden by subclasses")

	def _08_base_embed(self) -> Dict[str, Any]:
		return {
			"color": self.embed_color,
			"title": "A new Challenge has been registered!",
			"description": (
				"```diff\n"
				f"- Challenge № {self.key}\n"
				f"- Update {self.fecha}\n"
				"```"
			),
			# "timestamp": datetime.now(UTC).isoformat(),
			"timestamp": "TEST",
			"footer": {"text": "Let the challenges continue!"},
		}
		
	###--------------------ChallengeEvent.Private.Methods-------------###
	def __get_top10string(self):
		top10string = "\t\tTOP 10\n"
		# ic(self.chasys.top10list)
		for i in range(self.chasys.TOP_OF, -1, -1):	#iterar del 9 al 0
			if i >= len(self.chasys.top10list):
				continue
			player = self.chasys.top10list[i]
			top10string += f"\t{i+1:<4}. {player.name:20} {player.cha_wins}-{player.cha_loses}\n"
		return top10string
		
		
	###--------------------ChallengeEvent.Properties-------------###
	@cached_property
	def fecha(self):
		return self.date.strftime('%Y-%m-%d')
		
	@cached_property
	def replays_dir(self) -> Optional[Path]:
		return None
		
	@cached_property
	def games_total(self) -> int:
		return self.winner.wins + self.loser.wins
		
	@cached_property
	def games1v1(self) -> int:
		return self.winner.wins1v1 + self.loser.wins1v1
		
	@cached_property
	def games2v2(self) -> int:
		return self.winner.wins2v2 + self.loser.wins2v2
			
	@cached_property
	def challenger(self: "ChallengeEvent") -> "PlayerInChallenge":
		return self.winner if self.winner.rank > self.loser.rank else self.loser

	@cached_property
	def defender(self) -> "PlayerInChallenge":
		return self.winner if self.challenger is self.loser else self.loser
		
	
	###--------------------ChallengeEvent.Dunder.Methods----------------###
	def __lt__(self: "ChallengeEvent", other: "ChallengeEvent"):
		return self.key < other.key
		
	def __repr__(self: "ChallengeEvent"):
		return f"|Cha{self.key}|{self.version}|{self.winner}{self.winner.wins}|{self.loser}{self.loser.wins}|"
		
	def __str__(self: "ChallengeEvent"):
		return (
			"\n------------------------------------"
			f"\n{self.replays_dir.stem if self.replays_dir else 'NO_GAMES_NO_REPLAYS'}"
			"\n```diff\n"
			f"\n- Challenge № {self.key}"
			f"\n- Update {self.fecha}"
			f"{self._04_get_my_report()}"
			f"\n\nLet the challenges continue!"
			f"\n\n{self.top10string}```"
		)
		




#------------------------------------------------------------------------------------------#
#"""---------------------------------NormalChallenge.Class.02----------------------------"""#
#------------------------------------------------------------------------------------------#
class NormalChallenge(ChallengeEvent):
	
	###--------------------NormalChallenge.Properties-------------###
	@cached_property
	def embed(self) -> Dict[str, Any]:
		score = f"- **Score 1vs1**: {self.winner.wins1v1}-{self.loser.wins1v1} for **{self.winner.history.name}**"
		if self.games2v2:
			score += (
				f"\n- **Score 2vs2**: {self.winner.wins2v2}-{self.loser.wins2v2} for **{self.winner.history.name}**"
				f"\n- **Total Score**: {self.winner.wins}-{self.loser.wins} for **{self.winner.history.name}**"
			)
		embed: Dict[str, Any] = self._08_base_embed() | {
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
					"value": f"```diff\n{self.top10string}```",
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
		return embed
		
	@cached_property
	def replays_dir(self):
		return self.chasys.chareps / f"Challenge{self.key}_{self.challenger.history.key}_vs_{self.defender.history.key},_{self.challenger.wins}-{self.defender.wins},_{self.version}.rar"
		
	###--------------------NormalChallenge.Protected.Methods-------------###
	def _init_01_integrity_check(self) -> None:
		"NormalChallenge - don't log me retarded numbers"
		if not self.games_total:
			raise Exception(f"Error en el csv. Los jugadores deben tener juegos en un challenge tipo {self.version}.")
		if self.winner.wins <= self.loser.wins:
			raise Exception(f"Error de integridad: Como es posible que el ganador no tenga mas victorias que el perdedor?")
			
	def _init_02_impact_players_historial(self) -> None:
		"NormalChallenge is the only one that impacts historial"
		self.winner.history.append_cha(self)
		self.loser.history.append_cha(self)
		self.winner.history.append_cha_win_lose(self.winner)
		self.loser.history.append_cha_win_lose(self.loser)
		
	def _init_03_impact_system_top10_rank(self) -> None:
		"NormalChallenge - winner_takes_over"
		if self.challenger is self.winner:
			self.chasys._apply_a_take_over(self)

	def _04_get_my_report(self) -> str:
		def __report_01_report_defenseortakeover():
			flawlessly = "flawlessly " if self.loser.wins == 0 else ""
			if self.defender is self.winner:
				return f"\n\n+ {self.defender.history.name} has {flawlessly}defended the {self.defender.rank_ordinal} spot!"
			else:
				return f"\n\n+ {self.challenger.history.name} has {flawlessly}taken over the {self.defender.rank_ordinal} spot!"
				
		def __report_01_report_score():
			string = f"\nScore 1vs1: {self.winner.wins1v1}-{self.loser.wins1v1} for {self.winner.history.name}"
			if self.games2v2:
				string += (f"\nScore 2vs2: {self.winner.wins2v2}-{self.loser.wins2v2} for {self.winner.history.name}"
					f"\nScore: {self.winner.wins}-{self.loser.wins} for {self.winner.history.name}"
				)
			return string
			
		commment_line = f"\n\n\tComment: {self.notes}" if self.notes else ""
		return (
			f"{self._05_str_who_challenged_who()}"
			f"{__report_01_report_score()}"
			f"{__report_01_report_defenseortakeover()}"
			f"{commment_line}"
			f"\n\nGames were played in {self.version}"
		)
		
	def _05_str_who_challenged_who(self) -> str:
		"""Comportamiento normal + traditional chlng reference"""
		string = super()._05_str_who_challenged_who()
		if self.games2v2:
			string += "\nMode: Traditional challenge (4 games as 2vs2, 4 games as 1vs1, untie with 1vs1)."
		return string
		

	def _06_get_my_post(self, discord_message:str) -> requests.Response:
		response = requests.post(
			self.chasys.webhook_url,
			data={"content": discord_message},
			files={"file": open(self.replays_dir, "rb")}
		)
		if response.status_code != 200:
			return response
			
		webhook_message = response.json()
		message_id = webhook_message["id"]
		webhook_url_edit = f"{self.chasys.webhook_url}/messages/{message_id}"
		edit_payload: dict[str, Any] = {
			"content": discord_message,
			"embeds": [self.embed]
		}
		return requests.patch(
			webhook_url_edit,
			json=edit_payload
		)
	
	def _07_rename_existing_replaypack(self, torename:str, compress:bool) -> None:
		existing = self.chasys.chareps / torename
		if existing.exists() and not self.replays_dir.exists():
			existing.rename(self.chasys.chareps/self.replays_dir.name)
			print(f"* {torename} was renamed to {self.replays_dir.name}")
		# if compress:
			# ChallengeSystem.compress_folder(ideal)
	
	
	
	

#------------------------------------------------------------------------------------------#
#"""------------------------------NoScoreChallenge.Class.02------------------------"""#
#------------------------------------------------------------------------------------------#
class NoScoreChallenge(ChallengeEvent):
	
	###---------------NoScoreChallenge.Properties---------------###
	@cached_property
	def embed(self) -> Dict[str, Any]:
		return self._08_base_embed() | {
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
					"value": f"```diff\n{self.top10string}```",
					"inline": False
				}],
		}
	
	###---------------NoScoreChallenge.Protected.Methods---------------###
	def _init_01_integrity_check(self) -> None:
		"NoScoreChallenge - don't log me with games"
		if self.games_total:
			raise Exception(f"Error en el csv. Los jugadores deben tener 0 wins en un challenge tipo {self.version}.")
			
	def _init_02_impact_players_historial(self) -> None:
		"NoScoreChallenge is designed to not affect player winrate"
		self.winner.history.append_cha(self)
		self.loser.history.append_cha(self)
		
	def _04_get_my_report(self) -> str:
		commment_line = f"\n\n\tComment: {self.notes}" if self.notes else ""
		return (
			f"{self._05_str_who_challenged_who()}"
			f"\n\nSpotUndefended: {self.defender.history.name} has refused to defend his spot or hasn't arranged a play-date to defend it."
			f"\n\n+ {self.challenger.history.name} has taken over the {self.defender.rank_ordinal} spot!"
			f"{commment_line}"
			f"\n\nNo wins or losses have been scored."
		)
			
	def _06_get_my_post(self, discord_message:str) -> requests.Response:
		if self.notes:
			self.embed["fields"].insert(-2,{
				"name": "Comments: ",
				"value": f"*- {self.notes}*",
				"inline": False
			})
		payload: dict[str, Any] = {
			"content": discord_message,
			"embeds": [self.embed]
		}
		return requests.post(self.chasys.webhook_url, json=payload)
			
	def _07_rename_existing_replaypack(self, torename:str, compress:bool) -> None:
		return None
		
	

#------------------------------------------------------------------------------------------#
#"""------------------------------NoScoreChallenge.Class.02------------------------"""#
#------------------------------------------------------------------------------------------#
class KickAddChallenge(ChallengeEvent):
	
	###----------------KickAddChallenge.Protected.Properties-------------###
	@cached_property
	def embed(self) -> Dict[str, Any]:
		return self._08_base_embed() | {
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
					"value": f"```diff\n{self.top10string}```",
					"inline": False
				}
			],
		}
		
	###----------------KickAddChallenge.Protected.Methods-------------###
	def _init_01_integrity_check(self) -> None:
		"NoScoreChallenge - don't log me with games"
		if self.games_total:
			raise Exception(f"Error en el csv. Los jugadores deben tener 0 wins en un challenge tipo {self.version}.")
		
	def _init_02_impact_players_historial(self) -> None:
		"KickAddChallenge is designed to not affect player winrate"
		self.winner.history.append_cha(self)
		self.loser.history.append_cha(self)
		
	def _init_03_impact_system_top10_rank(self) -> None:
		"KickAddChallenge - unique method"
		self.chasys._apply_a_kick_add(self)
		
	def _04_get_my_report(self) -> str:
		commment_line = f"\n\n\tComment: {self.notes}" if self.notes else ""
		return (
			f"{self._05_str_who_challenged_who()}"
			f"\n\nAddAndKickUpdate: "
			f"Since Challenge {self.defender.previous_challenge.key}, {self.defender.history.name} has not played any game or challenge in {self.defender.days_since_last_chall} days."
			f"\n\n- {self.defender.history.name} has been kicked from the {self.defender.rank_ordinal} spot and from the list."
			f"\n\n+ {self.challenger.history.name} has been added to the top10 list, starting in the 10th spot."
			f"{commment_line}"
			f"\n\nNo wins or losses have been scored."
		)
		
		
	def _05_str_who_challenged_who(self) -> str:
		"""in Kick add Mode noone challenged anyone"""
		return ""	
			
			
	def _06_get_my_post(self, discord_message:str) -> requests.Response:
		if self.notes:
			self.embed["fields"].insert(-2,{
				"name": "Comments: ",
				"value": f"*- {self.notes}*",
				"inline": False
			})
		payload:dict[str, Any] = {
			"content": discord_message,
			"embeds": [self.embed]
		}
		return requests.post(self.chasys.webhook_url, json=payload)

			
	def _07_rename_existing_replaypack(self, torename:str, compress:bool) -> None:
		return None


#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------PlayerInChallenge.Class.03--------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#

class PlayerInChallenge:
	def __init__(self, challenge: ChallengeEvent, key: str, wins1v1: str, wins2v2: str):
		self.challenge = challenge
		self.history = self.challenge.chasys.PLAYERS[key]
		self.wins1v1 = int(wins1v1)
		self.wins2v2 = int(wins2v2)
		self.rank = self.challenge.chasys._get_index_or_append_if_new(self.history)
	###----------------PlayerInChallenge.Properties-------------###
	@cached_property
	def wins(self):
		return self.wins1v1 + self.wins2v2
		
	@cached_property
	def previous_challenge(self):
		return self.history.challenges[self.history.challenges.index(self.challenge)-1]
		
	@cached_property
	def days_since_last_chall(self):
		return (self.challenge.date - self.previous_challenge.date).days
		
	@cached_property
	def rank_ordinal(self):
		ordinal = { 
			0: "1st", 1: "2nd", 2: "3rd", 3: "4th", 4: "5th", 5: "6th", 6: "7th", 7: "8th", 8: "9th", 
			9: "10th",
			10: "11th",
			11: "12th",
			12: "13th",
			13: "14th",
			14: "15th",
		
		}
		
		return ordinal.get(self.rank, "from outside the list")

	###--------------------PlayerInChallenge.Dunder.Methods----------------###
	def __repr__(self):
		return f"|{self.history.key}|"




#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------ChallengeSystem.Class.04-----------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#

class ChallengeSystem:
	TOP_OF = 9 # 14 # 20
	def __init__(self, chareps: Path, chacsv: Path, chalog: Path, status: Path, players_json: Path, webhook_url:str):
		player_data: dict[str, dict[str, dict[str, list[str]]]] = json.load(open(players_json))
		self.chareps = chareps
		self.chacsv = chacsv
		self.chalog = chalog
		self.status = status
		self.webhook_url = webhook_url
		self.PLAYERS:dict[str, PlayerHistory] = self.__read_PLAYERS(player_data["active_players"])
		self.top10list:list[PlayerHistory] = list(map(lambda x: self.PLAYERS[x], player_data["legacy"]["top10"]))
		self.CHALLENGES: dict[int, ChallengeEvent] = self.__read_CHALLENGES()
		
		
	###----------------ChallengeSystem.Protected.Methods------------###
	def _get_index_or_append_if_new(self: "ChallengeSystem", player:PlayerHistory):
		try:
			return self.top10list.index(player)
		except ValueError:
			self.top10list.append(player)
			return self.top10list.index(player)
	
	
	def _apply_a_kick_add(self: "ChallengeSystem", challenge:ChallengeEvent):
		if not isinstance(challenge, KickAddChallenge):
			raise Exception(f"Wtf class? {type(challenge)}")
		self.top10list.remove(challenge.loser.history)
		self.top10list.remove(challenge.winner.history)
		self.top10list.insert(self.TOP_OF, challenge.loser.history)
		self.top10list.insert(self.TOP_OF, challenge.winner.history)
			
			
	def _apply_a_take_over(self: "ChallengeSystem", challenge:ChallengeEvent):
		if not isinstance(challenge, (NormalChallenge, NoScoreChallenge)):
			raise Exception(f"Wtf class? {type(challenge)}")
		self.top10list.remove(challenge.winner.history) 
		self.top10list.insert(challenge.loser.history.get_rank(), challenge.winner.history) 
		
	###----------------ChallengeSystem.Public.Methods------------###
	def write_csv(self: "ChallengeSystem"):
		# if not get_boolean("Are you sure you want to re-write the .csv database? You better have a backup"):
			# return
			
		supastring = "key;version;w_key;w_wins1v1;w_wins2v2;l_key;l_wins1v1;l_wins2v2;date;notes\n"
		for cha in reversed(list(self.CHALLENGES.values())):
			supastring += cha.as_row()

		with open(self.chacsv, mode='w', newline='', encoding='latin1') as file:
			file.write(supastring)
		print(".csv guardado.")

	def write_status(self: "ChallengeSystem"):
		super_string = "\n".join(str(player.get_status()) for player in sorted( self.PLAYERS.values() ))
		with open(self.status, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.status.name} was updated")
			
	def write_embeds(self: "ChallengeSystem"):
		all_instances = {cha.key: cha.embed for cha in reversed(self.CHALLENGES.values())}
		filepath = r"output\embeds.json"
		with open(filepath, "w") as json_file:
			json.dump(all_instances, json_file, indent=4)
			
			
	def write_chalog(self: "ChallengeSystem"):
		# super_string = f"##AutoGenerated by 'ChallengeSystem' {datetime.today().strftime("%Y-%m-%d")}\nRegards, Bambi\n\n"
		super_string = f"##AutoGenerated by 'ChallengeSystem'\nRegards, Bambi\n\n"
		for num, cha in enumerate( sorted( self.CHALLENGES.values(),reverse=True ) , start=1):
			if num == 1:
				cha._07_rename_existing_replaypack("torename.rar", compress=False)
				print(cha)
			super_string += str(cha)
		
		with open(self.chalog, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.chalog.name} was updated")
	
	def send_all_posts(self: "ChallengeSystem", confirmed:bool, start_with:int, finish_at: int, initial_delay: int, delay_between: int):
		if not confirmed and not get_boolean(f"Confirm do you want recursively post challenges between {start_with}-{finish_at} in {initial_delay} minutes each {delay_between} minutes"):
			return
		self.CHALLENGES[start_with].post(confirmed=True, delay=initial_delay)
		for chakey in range(start_with+1, finish_at+1):
			self.CHALLENGES[chakey].post(confirmed=True, delay=delay_between)
			
	def execute_argv_operations_if_any(self: "ChallengeSystem", argv: list[str]):
		min_chall = min(self.CHALLENGES)
		max_chall = max(self.CHALLENGES)
		def __get_validated_argv_dict(argv: list[str]) -> dict[str, Any]:
			argv_dict: dict[str, Any] = {
				"cha_id": None,
				"post": None,
				"post_all": None,
				"confirmed": False,
			}
			if len(argv) > 2:
				if argv[1].isnumeric():
					cha_id = int(argv[1])
					if min_chall <= cha_id <= max_chall:
						argv_dict["cha_id"] = cha_id
					else:
						raise Exception(f"Challenge out of the range {min_chall}-{max_chall} range.")
				else:
					raise Exception(f"Wrong argv: {argv[1]} is not a valid challenge id")
				if argv[2] not in argv_dict:
					raise Exception(f"Wrong argv: {argv[2]} is not a valid method")
				else:
					argv_dict[argv[2]] = True
			return argv_dict	
		
		if len(argv) != 1:
			argv_dict = __get_validated_argv_dict(argv)
		else:
			argv_dict: dict[str, Any] = {
				"cha_id": get_int("Insertar challenge id: ", min=min_chall, max=max_chall),
				"post_all": get_boolean("Post all? "),
				"post": get_boolean("Post one? "),
				"delay": get_int("Initial delay?: "),
				"confirmed": True,
			}
		
		if argv_dict["post"]:
			instance = self.CHALLENGES[argv_dict["cha_id"]]
			instance.post(
				confirmed=argv_dict["confirmed"], 
				delay=argv_dict["delay"]
			)
		elif argv_dict["post_all"]:
			self.send_all_posts(
				confirmed=argv_dict["confirmed"],
				start_with=argv_dict["cha_id"], 
				finish_at=min_chall, 
				initial_delay=argv_dict["delay"], 
				delay_between=7,
			)

	def get_challenge(self: "ChallengeSystem", hint: Optional[int]) -> ChallengeEvent:
		min=1
		max=len(self.CHALLENGES)
		if hint is None:
			return self.CHALLENGES[get_int(f"Select challenge. Type the ID (min: {min}, max:{max}): ", indent=0, min=min, max=max)]
		elif result := self.CHALLENGES.get(cast(int, hint)):
			return result
		else:
			raise Exception(f"Challenge of id {hint} not found. Logged challenges are between {min} and {max}.")

	def consult_03_player_vs_player(self:"ChallengeSystem", p1_key:str, p2_key:str, print_em:bool):
		return self.PLAYERS[p1_key].get_1v1_vs(self.PLAYERS[p2_key], print_em=print_em)
		
	# def consult_04_who_is_black(self, pname):
		# ic(self.PLAYERS[pname].is_black)
	
	# def consult_05_2v2_score(self, pname):
		# ic(self.PLAYERS[pname].wins2v2_total)
		# ic(self.PLAYERS[pname].loses2v2_total)

	
	###----------------ChallengeSystem.Private.Methods------------###
	def __read_CHALLENGES(self: "ChallengeSystem") -> dict[int, ChallengeEvent]:
		def sorted_dict_of_chall_from_lines(lines: list[str]):
			headers = lines[0].strip().split(';')
			rows = [line.strip().split(';') for line in lines[1:]]
			key_column = 0 #the column that says KEY
			sorted_rows = sorted(rows, key=lambda row: int(row[key_column]))
			dataaaa:dict[int,ChallengeEvent] = {}
			for row in sorted_rows:
				row_dict = {headers[i]: row[i] for i in range(len(headers))}
				key = int(row_dict['key'])
				version = row_dict['version']
				dataaaa[key] = ChallengeEvent.new_from_row(self, key, version, row_dict)
			return dataaaa
			
		if not self.chacsv.exists() or self.chacsv.stat().st_size == 0:
			raise Exception(f"No existe {self.chacsv}")
			return
		else:
			with open(self.chacsv, mode='r', encoding='latin1') as file:
				lines: list[str] = file.readlines()
			return sorted_dict_of_chall_from_lines(lines)
		
	def __read_PLAYERS(self: "ChallengeSystem", active_players:dict[str,dict[str, list[str]]]) -> dict[str, PlayerHistory]:
		if self.chalog.exists():
			return { key: PlayerHistory(self, key, value) for key, value in active_players.items() }
		else:
			raise Exception(f"No existe {self.chalog}")
		
		
	###----------------ChallengeSystem.Static.Methods------------###
	# @staticmethod
	# def compress_folder(folder_path):
		# if folder_path.exists():
			# if not folder_path.is_dir():
				# raise ValueError("Input path must be a directory.")
			# archive_path = folder_path.with_suffix(".7z")
			# with py7zr.SevenZipFile(archive_path, 'w') as archive:
				# archive.writeall(folder_path)
			# print(f"* {folder_path.name} was 7ziped")
			
			
		
		
		
		
		
#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------------ok.Iniciar-------------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#

SISTEMA = ChallengeSystem(
	players_json = Path.cwd() / "data" / "players.json",
	chareps = Path(r"replays"),
	chacsv = Path(r"data/challenges.csv"),
	chalog = Path(r"output/challenges.log"),
	status = Path(r"output/status.log"),
	webhook_url = SECRETS.PIG_WEB_HOOK
)




	
if __name__ == "__main__":
	SISTEMA.write_chalog();
	SISTEMA.write_status();
	# SISTEMA.write_embeds();
	# SISTEMA.write_csv();
	
	
		
	"""1. Consultas functions"""
	# SISTEMA.consult_03_player_vs_player("ECTH", "ANDY", print_em=True)
	# SISTEMA.consult_03_player_vs_player("ECTH", "ASTRO", print_em=True)
	# SISTEMA.consult_03_player_vs_player("ECTH", "AHWE", print_em=True)
	# SISTEMA.consult_03_player_vs_player("ECTH", "YUSUF", print_em=True)
	# SISTEMA.consult_03_player_vs_player("ECTH", "ENUMA", print_em=True)
	# SISTEMA.consult_03_player_vs_player("ECTH", "GANNICUS", print_em=True)
	
	
	
	# SISTEMA.consult_03_player_vs_player("OTTO", "ANDY", print_em=True)
	# SISTEMA.consult_03_player_vs_player("OTTO", "AHWE", print_em=True)
	# SISTEMA.consult_03_player_vs_player("OTTO", "ECTH", print_em=True)
	
	
	# SISTEMA.consult_03_player_vs_player("OTTO", "ASTRO", print_em=True)
	# SISTEMA.consult_04_who_is_black()
	# SISTEMA.consult_05_2v2_score()
	
	"""2. Argv"""
		# python cha.py 312
		# python cha.py 314 post
		# python cha.py 314 post_till_end
	SISTEMA.execute_argv_operations_if_any(sys.argv);
	
	"""3. SendToChlngUpdates"""
	# SISTEMA.get_challenge(hint=None).post(confirmed=false, delay=0)


