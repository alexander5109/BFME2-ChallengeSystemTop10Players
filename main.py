from datetime import datetime
from pathlib import Path
import pandas as pd
from icecream import ic
import json
import py7zr
from functools import cached_property
from bidict import bidict
    
    
    
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
		self.version = row["version"]
		self.date = datetime.strptime(row["date"], '%Y-%m-%d')
		self.dateString = datetime.strptime(row["date"], '%Y-%m-%d').strftime('%Y-%m-%d')
		self.custom_msg = f"\n\n\tComment: {row['message']}" if pd.notna(row['message']) and row['message'] else ""
		self.player1 = PlayerInChallenge(self, row["p1"], row["p1wins1v1"], row["p1wins2v2"])
		self.player2 = PlayerInChallenge(self, row["p2"], row["p2wins1v1"], row["p2wins2v2"])
		
		self.__01_asegurar_row_integrity()
		self.__02_set_player_records()
		self.__03_set_player_ranks()
		self.__04_freeze_current_top_10_string()


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
		top_10_as_dict = {
			player.rank: player
			for player in self.chasys.PLAYERS.values()
			if 1 <= player.rank <= 10
		}
		self.top10 = "\t\tTOP 10\n"
		for rank, player in sorted(top_10_as_dict.items(), reverse=True):
			self.top10 += f"\t{rank:<4}. {player.name:20} {player.cha_wins}-{player.cha_loses}\n"



	###--------------------------Public.Properties-----------------------###
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
	def replays_folder_name(self):
		return f"Challenge{self.key}_{self.challenger.history.key} vs {self.defender.history.key}, {self.challenger.wins}-{self.defender.wins}, {self.version}"
		
	# @cached_property
	# def players_involved(self):
		# return {
			# self.winner.key: self.winner
			# self.loser.key: self.loses
		# }
		



			
	
	###--------------------------Public.dundermethod-----------------------###
	def __lt__(self, other):
		return self.key < other.key
		
	def __repr__(self):
		return f"|Cha{self.key}|{self.version}|{self.winner}{self.winner.wins}|{self.loser}{self.loser.wins}|"
		
	def __str__(self):
		# Helper methods for clarity
		def get_mode_description():
			if self.games2v2:
				return "\nMode: Traditional challenge (4 games as 2vs2, 4 games as 1vs1, untie with 1vs1)."
			return ""

		def get_02_score_1v1():
			if self.games1v1:
				return f"\nScore 1vs1: {self.winner.wins1v1}-{self.loser.wins1v1} for {self.winner.history.name}"
			return ""

		def get_03_score_2v2():
			if self.games2v2:
				return (
					f"\nScore 2vs2: {self.winner.wins2v2}-{self.loser.wins2v2} for {self.winner.history.name}"
					f"\nScore: {self.winner.wins}-{self.loser.wins} for {self.winner.history.name}"
				)
			return ""

		def get_04_add_and_kick_message():
			if self.is_kick_add_mode:
				since_last_event = f'Since Challenge {self.defender.previous_challenge.key}'
				return (
					f"\n\nAddAndKickUpdate: {since_last_event}, {self.defender.history.name} has not played any game "
					f"or challenge in {self.defender.days_since_last_chall} days."
					f"\n\n- {self.defender.history.name} has been kicked from the {self.defender.rank_ordinal} spot and from the list."
				)
			if self.is_no_score_mode:
				return f"\n\nSpotUndefended: {self.defender.history.name} has refused to defend his spot or hasn't arranged a play-date to defend it."
			return ""

		def get_01_challenge_message():
			if not self.is_kick_add_mode:
				return (
					f"\n\n{self.challenger.history.name} ({self.challenger.rank_ordinal}) has challenged "
					f"{self.defender.history.name} ({self.defender.rank_ordinal}) for his spot."
					f"{get_mode_description()}"
				)
			return ""

		def get_06_version_message():
			if self.games_total:
				return f"Games were played in {self.version}"
			return "No wins or losses have been scored."

		def get_05_defense_or_takeover_message():
			if self.is_kick_add_mode:
				return f"\n\n+ {self.challenger.history.name} has been added to the top10 list, starting in the 10th spot."

			flawless = "flawlessly " if self.loser.wins == 0 and not self.is_no_score_mode and not self.is_kick_add_mode else ""
			if self.defender is self.winner:
				return f"\n\n+ {self.defender.history.name} has {flawless}defended the {self.defender.rank_ordinal} spot!"
			return f"\n\n+ {self.challenger.history.name} has {flawless}taken over the {self.defender.rank_ordinal} spot!"

		# Assembling the message
		return (
			f"\n------------------------------------\n{self.replays_folder_name}\n```diff\n"
			f"\n- Challenge № {self.key}\n- Update {self.dateString}"
			f"{get_01_challenge_message()}"
			f"{get_02_score_1v1()}"
			f"{get_03_score_2v2()}"
			f"{get_04_add_and_kick_message()}"
			f"{get_05_defense_or_takeover_message()}"
			f"{self.custom_msg}"
			f"\n\n{get_06_version_message()}"
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
		self.wins1v1 = wins1v1
		self.wins2v2 = wins2v2
		self.wins = wins1v1 + wins2v2
		self.history = self.challenge.chasys.PLAYERS[key]
		self.history.challenges.append(self.challenge)
		self.rank = self.history.rank
			
			
			
	###--------------------------Public.Properties-----------------------###
	@cached_property
	def rank_ordinal(self):
		ordinal = { 1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th", 8: "8th", 9: "9th", 10: "10th"}
		return ordinal.get(self.rank, "from outside the list")
		
	@cached_property
	def previous_challenge(self):
		previous_index = self.history.challenges.index(self.challenge)-1
		return self.history.challenges[previous_index]
	
	@cached_property
	def days_since_last_chall(self):	
		return (self.challenge.date - self.previous_challenge.date).days
		
	###--------------------------Public.dundermethod-----------------------###
	def __repr__(self):
		return f"|{self.history.key}|"






#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------ChallengeSystem.Class.04-----------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class ChallengeSystem:
	def __init__(self, chacsv, chalog, status, player_data, write_log=False, write_csv=False):
		if not chacsv.exists():
			raise Exception("No existe el archivo de los .csv")
		if not chalog.exists():
			raise Exception("No existe el archivo de los .log")
		self.chacsv = chacsv
		self.chalog = chalog
		self.status = status
		self.__do_01_read_csv()
		
		
		legacy = bidict({int(key): value for key, value in player_data["legacy"]["top10"].items()})
		self.PLAYERS = { key: Player.instance_with_rank(key, value, legacy) for key, value in player_data["active"].items() }
		self.CHALLENGES = { key: ChallengeEvent(self, key, row) for key, row  in self.data.iterrows() }
		if write_log:
			self.__do_02_write_chalog()
		if write_csv:
			self.__do_03_write_csv(reverse=False)
		self.__do_04_write_status()
		
	###--------------------------Public.Methods-----------------------###

	def consult_03_player_vs_player(self, p1_key, p2_key, print_em):
		return self.PLAYERS[p1_key].get_1v1_vs(self.PLAYERS[p2_key], print_em=print_em)
		
	def consult_04_who_is_black(self, pname):
		ic(self.PLAYERS[pname].is_black)
	
	def consult_05_2v2_score(self, pname):
		ic(self.PLAYERS[pname].wins2v2_total)
		ic(self.PLAYERS[pname].loses2v2_total)

	
	###--------------------------Private.Methods-----------------------###
	def __do_01_read_csv(self):
		if self.chacsv.exists() and self.chacsv.stat().st_size >0 :
			self.data = pd.read_csv(self.chacsv, sep = ";", encoding = "latin1")
		else:
			self.data = pd.DataFrame(columns=['key','version','p1','p1wins1v1','p1wins2v2','p2','p2wins1v1','p2wins2v2','date'])
		self.data.set_index('key', inplace=True)
		self.data.sort_index(inplace=True, ascending=True)
		
	def __do_02_write_chalog(self):
		super_string = f"##AutoGenerated by 'ChallengeSystem' {datetime.today().strftime("%Y-%m-%d")}\nRegards, Bambi\n\n"
		
		for num, cha in enumerate( sorted( self.CHALLENGES.values(),reverse=True ) , start=1):
			if num == 1:
				ChallengeSystem.rename_folder("torename", cha.replays_folder_name, compress=False)
				print(cha)
			super_string += str(cha)
		
		with open(self.chalog, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.chalog.name} was updated")
		
	def __do_03_write_csv(self, reverse):
		if reverse:
			self.data.sort_index(inplace=True, ascending=False)
		self.data.to_csv(self.chacsv, sep = ";", index = True, decimal = ",", encoding = "latin1")
		print(".csv guardado.")

	def __do_04_write_status(self):
		super_string = "\n".join(str(player) for player in sorted( self.PLAYERS.values() ))
		with open(self.status, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.status.name} was updated")

	###------------------------------Statics-----------------------###
	@staticmethod
	def compress_folder(folder_path):
		if folder_path.exists():
			if not folder_path.is_dir():
				raise ValueError("Input path must be a directory.")
			archive_path = folder_path.with_suffix(".7z")
			with py7zr.SevenZipFile(archive_path, 'w') as archive:
				archive.writeall(folder_path)
			print(f"* {folder_path.name} was 7ziped")


	@staticmethod
	def rename_folder(torename, ideal, compress):
		existing = Path(rf"D:\MEGA\BFME2 - Ecthelion Replays\_ChallengueLeage_Replays\{torename}")
		ideal = Path(rf"D:\MEGA\BFME2 - Ecthelion Replays\_ChallengueLeage_Replays\{ideal}")
		if existing.exists() and not ideal.exists():
			existing.rename(ideal)
			print(f"* {torename} was renamed to {ideal.name}")
		if compress:
			ChallengeSystem.compress_folder(ideal)
			
			
		
		
		
		
		
#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------------ok.Iniciar-------------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
	sistema = ChallengeSystem(
		player_data = json.load(open("players.json")),
		chacsv=Path.cwd() / "challenges.csv",
		chalog=Path.cwd() / "challenges.log",
		status=Path.cwd() / "status.log",
		write_log=True,
		write_csv=False
	)

	"""4. Consultas functions"""
	# sistema.consult_03_player_vs_player()
	# sistema.consult_04_who_is_black()
	# sistema.consult_05_2v2_score()
	