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
	def add_challenge_record(self, challenge):
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
		
	###--------------------------Private.Methods-----------------------###
	def __get_cha_winrate(self):
		if self.cha_wins == 0:
			return 0
		total_matches = self.cha_wins + self.cha_loses
		assert total_matches == len(self.challenges)
		return (self.cha_wins / total_matches) * 100.0

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
		
	@cached_property
	def is_black(self):
		return True if self.key in {PLAYERS["ANDY"].key, PLAYERS["LAU"].key} else False

	def __gt__(self, other):
		bol = self.get_1v1_vs(other, print_em=False)
		if bol is None:
			bol = self.__get_cha_winrate()  > other.__get_cha_winrate()
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
		
		self.__01_asegurar_integridad_de_row()
		self.__02_compute_logic()
		self.__03_freeze_current_top_10_string()


	###--------------------------Private.Methods-----------------------###
	def __01_asegurar_integridad_de_row(self):
		if not self.is_normal_mode and self.games_total:
			raise Exception(f"Error en el csv. Los jugadores deben tener 0 wins en un challenge tipo {self.version}.")
		
	
	def __02_compute_logic(self):
		if self.is_normal_mode:
			self.winner.history.add_challenge_record(self)
			self.loser.history.add_challenge_record(self)
			
		if self.challenger is not self.winner:
			return
			
		self.challenger.history.rank = 10 if self.is_kick_add_mode else self.defender.rank
		self.defender.history.rank += len(self.chasys.PLAYERS) if self.is_kick_add_mode else 1 
		
		for player in self.chasys.PLAYERS.values():
			if player.key in {self.winner.key, self.loser.key}:
				continue
			elif player.rank > self.winner.rank:
				player.rank -= 1
				
			if self.is_kick_add_mode and 11 > player.rank > self.loser.rank:
				player.rank -= 1
			elif player.rank > self.loser.rank:
				player.rank += 1
			
			
	def __03_freeze_current_top_10_string(self):
		top_10_as_dict = {
			player.rank: player
			for player in self.chasys.PLAYERS.values()
			if 1 <= player.rank <= 10
		}
		self.top10 = "\t\tTOP 10\n"
		for rank, player in sorted(top_10_as_dict.items(), reverse=True):
			self.top10 += f"\t{rank:<4}. {player.name:20} {player.cha_wins}-{player.cha_loses}\n"

	###--------------------------Public.Properties-----------------------###
	# @cached_property
	# def players_involved(self):
		# return {
			# self.winner.key: self.winner
			# self.loser.key: self.loses
		# }
	
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
	def str_bo9_or_b4b5(self):
		if not self.games2v2:
			# return "Challenge Mode: Best of 9 in 1vs1."
			return ""
		else:
			return "\nMode: Traditional challenge (4 games as 2vs2, 4 games as 1vs1, untie with 1vs1)."
		
	@cached_property
	def str_challenge_or_none(self):
		if not self.is_kick_add_mode:
			return f"\n\n{self.challenger.history.name} ({self.challenger.rank_ordinal}) has challenged {self.defender.history.name} ({self.defender.rank_ordinal}) for his spot.{self.str_bo9_or_b4b5} "
		else:
			return ""
		
	@cached_property
	def str_score1v1_or_none(self):
		return f"\nScore 1vs1: {self.winner.wins1v1}-{self.loser.wins1v1} for {self.winner.history.name}" if self.games1v1 else ""
		
	@cached_property
	def str_score2v2_or_none(self):
		return f"\nScore 2vs2: {self.winner.wins2v2}-{self.loser.wins2v2} for {self.winner.history.name}\nScore: {self.winner.wins}-{self.loser.wins} for {self.winner.history.name}" if self.games2v2 else ""
		
	@cached_property
	def str_add_and_kick_or_none(self):
		if self.is_kick_add_mode:
			since_last_event = f'Since Challenge{self.defender.previous_challenge.key}'
			return f"{f"\n\nAddAndKickUpdate: {since_last_event}, {self.defender.history.name} has not played any game or challenge in {self.defender.days_since_last_chall} days."}{f"\n\n- {self.defender.history.name} has been kicked from the {self.defender.rank_ordinal} spot and from the list." }"
		elif self.is_no_score_mode:
			return f"\nSpotUndefended: {self.defender.history.name} has refused to defend his spot or hasn't bothered to arrange a play-date to defend his spot."
		else:
			return ""
		
	@cached_property
	def str_defended_or_took_over(self):
		if self.is_kick_add_mode:
			return f"\n\n+ {self.challenger.history.name} has been added to the top10 list, begining on the 10th spot."
			
		flawless = "flawlessly " if self.loser.wins == 0 and not self.is_no_score_mode and not self.is_kick_add_mode else ""
		if self.defender is self.winner:
			return f"\n\n+ {self.defender.history.name} has {flawless}defended the {self.defender.rank_ordinal} spot!"
		else:
			return f"\n\n+ {self.challenger.history.name} has {flawless}took over the {self.defender.rank_ordinal} spot!" 
		
	@cached_property
	def str_version_or_no_score(self):
		if self.games_total:
			return f"\n\nGames were played in {self.version}"
		else:
			return "\n\nNo wins or loses have been scored."
		
	@cached_property
	def replays_folder_name(self):
		return f"Challenge{self.key}_{self.challenger.history.key} vs {self.defender.history.key}, {self.challenger.wins}-{self.defender.wins}, {self.version}"
		
	def __repr__(self):
		return f"|Cha{self.key}|{self.version}|{self.winner}{self.winner.wins}|{self.loser}{self.loser.wins}|"

	def __str__(self):
		return f"\n------------------------------------\n{self.replays_folder_name}\n```diff\n\n- Challenge № {self.key}\n- Update {self.dateString}{self.str_challenge_or_none}\n{self.str_score1v1_or_none}{self.str_score2v2_or_none}{self.str_add_and_kick_or_none}{self.str_defended_or_took_over}{self.custom_msg}{self.str_version_or_no_score}\n\nLet the challenges continue!\n\n{self.top10}```"








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
		ordinal = {
			1: "1st",
			2: "2nd",
			3: "3rd",
			4: "4th",
			5: "5th",
			6: "6th",
			7: "7th",
			8: "8th",
			9: "9th",
			10: "10th"
		}
		return ordinal.get(self.rank, "from outside the list")
		
	@cached_property
	def previous_challenge(self):
		previous_index = self.history.challenges.index(self.challenge)-1
		return self.history.challenges[previous_index]
	
	@cached_property
	def days_since_last_chall(self):	
		return (self.challenge.date - self.previous_challenge.date).days
		
	def __repr__(self):
		return f"|{self.history.key}|"






#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------ChallengeSystem.Class.04-----------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class ChallengeSystem:
	def __init__(self, chacsv, chalog, player_data, write_log=False, write_csv=False):
		if not chacsv.exists():
			raise Exception("No existe el archivo de los .csv")
		if not chalog.exists():
			raise Exception("No existe el archivo de los .log")
		self.chacsv = chacsv
		self.chalog = chalog
		
		
		legacy = bidict({int(key): value for key, value in player_data["legacy"]["top10"].items()})
		self.PLAYERS = { key: Player.instance_with_rank(key, value, legacy) for key, value in player_data["active"].items() }
		self.CHALLENGES = { key: ChallengeEvent(self, key, row) for key, row  in self.data.iterrows() }
		if write_log:
			self.__write_chalog()
		if write_csv:
			self.__write_csv(reverse=False)
		
	###--------------------------Public.Methods-----------------------###
	def consult_01_challenge_log(self, reverse=False):
		for cha in self.sorted_challenges(reverse).values():
			print(cha)
			
	def consult_03_player_vs_player(self, p1_key, p2_key, print_em):
		return self.PLAYERS[p1_key].get_1v1_vs(self.PLAYERS[p2_key], print_em=print_em)
		
	def consult_04_who_is_black(self, pname):
		ic(self.PLAYERS[pname].is_black)
	
	def consult_05_2v2_score(self, pname):
		ic(self.PLAYERS[pname].wins2v2_total)
		ic(self.PLAYERS[pname].loses2v2_total)

	
	###--------------------------Private.Methods-----------------------###
	def sorted_challenges(self, reverse):
		return {key: value for key, value in sorted(self.CHALLENGES.items(), reverse=reverse)}
		
	def __write_csv(self, reverse):
		if reverse:
			data.sort_index(inplace=True, ascending=False)
		data.to_csv(self.chacsv, sep = ";", index = True, decimal = ",", encoding = "latin1")
		print(".csv guardado.")

	def __write_chalog(self):
		super_string = f"##AutoGenerated by 'ChallengeSystem' {datetime.today().strftime("%Y-%m-%d")}\nRegards, Bambi\n\n"
		for num, cha in enumerate(self.sorted_challenges(reverse=True).values(), start=1):
			if num == 1:
				ChallengeSystem.__rename_folder("torename", cha.replays_folder_name, compress=False)
				print(cha)
			super_string += str(cha)
		
		with open(self.chalog, "w", encoding='utf-8') as file:
			file.write(super_string)
			print(f"* {self.chalog.name} was updated")


	###------------------------------Statics-----------------------###
	@staticmethod
	def __compress_folder(folder_path):
		if folder_path.exists():
			if not folder_path.is_dir():
				raise ValueError("Input path must be a directory.")
			archive_path = folder_path.with_suffix(".7z")
			with py7zr.SevenZipFile(archive_path, 'w') as archive:
				archive.writeall(folder_path)
			print(f"* {folder_path.name} was 7ziped")


	@staticmethod
	def __rename_folder(torename, ideal, compress):
		existing = Path(rf"D:\MEGA\BFME2 - Ecthelion Replays\_ChallengueLeage_Replays\{torename}")
		ideal = Path(rf"D:\MEGA\BFME2 - Ecthelion Replays\_ChallengueLeage_Replays\{ideal}")
		if existing.exists() and not ideal.exists():
			existing.rename(ideal)
			print(f"* {torename} was renamed to {ideal.name}")
		if compress:
			ChallengeSystem.__compress_folder(ideal)
			
			
	###------------------------------Properties-----------------------###
	
	@cached_property
	def data(self):
		if self.chacsv.exists() and self.chacsv.stat().st_size >0 :
			data = pd.read_csv(self.chacsv, sep = ";", encoding = "latin1")
		else:
			data = pd.DataFrame(columns=['key','version','p1','p1wins1v1','p1wins2v2','p2','p2wins1v1','p2wins2v2','date'])
		data.set_index('key', inplace=True)
		data.sort_index(inplace=True, ascending=True)
		return data
			
	

#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------------ok.Iniciar-------------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
	sistema = ChallengeSystem(
		player_data = json.load(open("players.json")),
		chacsv=Path.cwd() / "challenges.csv",
		chalog=Path.cwd() / "challenges.log",
		write_log=True,
		write_csv=False
	)

	"""4. Consultas functions"""
	# sistema.consult_01_challenge_log(reverse=False)
	# sistema.consult_03_player_vs_player()
	# sistema.consult_04_who_is_black()
	# sistema.consult_05_2v2_score()
	