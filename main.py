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
		self.discord_id = value["discord_id"]

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
#"""---------------------------------------Challenge.Class.02----------------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class Challenge:
	def __init__(self, chasys, index, row):
		self.chasys = chasys
		self.index = index
		self.version = row["version"]
		self.date = datetime.strptime(row["date"], '%Y-%m-%d')
		self.dateString = datetime.strptime(row["date"], '%Y-%m-%d').strftime('%Y-%m-%d')
		self.dont_score_mode = self.version == "NO_SCORE"
		self.is_add_and_kick = self.version == "ADD_AND_KICK"
		if not self.dont_score_mode and not self.is_add_and_kick:
			player1 = PlayerInChallenge(self, row["p1"], row["p1wins1v1"], row["p1wins2v2"])
			player2 = PlayerInChallenge(self, row["p2"], row["p2wins1v1"], row["p2wins2v2"])
			self.winner = player2 if player2.wins > player1.wins else player1
			self.loser = player1 if self.winner == player2 else player2
		else:
			player1 = PlayerInChallenge(self, row["p1"], 0, 0)
			player2 = PlayerInChallenge(self, row["p2"], 0, 0)
			self.winner = player1 
			self.loser = player2 
		self.games_total = self.winner.wins + self.loser.wins
		self.games1v1 = self.winner.wins1v1 + self.loser.wins1v1
		self.games2v2 = self.winner.wins2v2 + self.loser.wins2v2
		
			
		self.challenger = player1 if player1.rank > player2.rank else player2
		self.defender = player1 if self.challenger == player2 else player2
		self.everyone_else_on_list = {player for player in self.chasys.PLAYERS.values() if player.key not in {self.winner.key, self.loser.key}}
		self.custom_msg = f"\n\n\tComment: {row['message']}" if row['message'] else ""
		self.flawless = "flawlessly " if self.loser.wins == 0 and not self.dont_score_mode and not self.is_add_and_kick else ""
		
		if self.dont_score_mode:
			self.__update_histories(issue_score=False)
		elif self.str_add_and_kick_or_none:
			self.__add_p1_kick_p2()
		elif self.games_total:
			self.__update_histories(issue_score=True)	
			
		self.top10 = self.__save_current_top_10()
		self.disputed_rank = self.defender.rank
		
	###--------------------------Private.Methods-----------------------###
	def __add_p1_kick_p2(self):
		last_spot = len(self.chasys.PLAYERS)
		if self.winner.rank > self.loser.rank:
			for player in self.everyone_else_on_list:
				if player.rank > self.winner.rank:
					player.rank -= 1
				if self.loser.rank < player.rank < 11:
					player.rank -= 1
			self.winner.history.rank = 10 
			self.loser.history.rank += last_spot # 
			
	def __save_current_top_10(self):
		top_10_as_dict = {
			player.rank: player
			for player in self.chasys.PLAYERS.values()
			if 1 <= player.rank <= 10
		}
		as_string = "\t\tTOP 10\n"
		for rank, player in sorted(top_10_as_dict.items(), reverse=True):
			as_string += f"\t{rank:<4}. {player.name:20} {player.cha_wins}-{player.cha_loses}\n"
		return as_string
	
	
	def __update_histories(self, issue_score):
		if self.winner.history.rank > self.loser.history.rank:
			for player in self.everyone_else_on_list:
				if player.rank > self.winner.history.rank:
					player.rank -= 1
				if player.rank > self.loser.history.rank:
					player.rank += 1
			self.winner.history.rank = self.loser.history.rank
			self.loser.history.rank += 1
		if issue_score:
			self.winner.history.cha_wins += 1
			self.loser.history.cha_loses += 1
				
			
			self.winner.history.games_played_total += self.games_total
			self.winner.history.games_played_1v1 += self.games1v1
			self.winner.history.games_played_2v2 += self.games2v2
			self.winner.history.wins_total += self.winner.wins
			self.winner.history.wins1v1_total += self.winner.wins1v1
			self.winner.history.wins2v2_total += self.winner.wins2v2
			
			self.loser.history.games_played_total += self.games_total
			self.loser.history.games_played_1v1 += self.games1v1
			self.loser.history.games_played_2v2 += self.games2v2
			self.loser.history.wins_total += self.loser.wins
			self.loser.history.wins1v1_total += self.loser.wins1v1
			self.loser.history.wins2v2_total += self.loser.wins2v2


	###--------------------------Public.Properties-----------------------###
	@cached_property
	def is_cha(self):
		return not self.str_add_and_kick_or_none and not self.dont_score_mode
		
	@cached_property
	def str_bo9_or_b4b5(self):
		if not self.games2v2:
			# return "Challenge Mode: Best of 9 in 1vs1."
			return ""
		else:
			return "\nMode: Traditional challenge (4 games as 2vs2, 4 games as 1vs1, untie with 1vs1)."
		
	@cached_property
	def str_challenge_or_none(self):
		if not self.is_add_and_kick: #self.is_cha:
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
		if self.is_add_and_kick:
			since_last_event = f'Since Challenge{self.defender.last_challenge.index}' #if self.defender.last_challenge else f'Since added in the top10 list in the ChallengeEvent{self.defender.fecha_de_alta}'
			return f"{f"\n\nAddAndKickUpdate: {since_last_event}, {self.defender.history.name} has not played any game or challenge in {self.defender.days_since_last_chall} days."}{f"\n\n- {self.defender.history.name} has been kicked from the {self.defender.rank_ordinal} spot and from the list." }"
		elif self.dont_score_mode:
			return f"\nSpotUndefended: {self.defender.history.name} has refused to defend his spot or hasn't bothered to arrange a play-date to defend his spot."
		else:
			return ""
		
	@cached_property
	def str_defended_or_took_over(self):
		if self.is_add_and_kick:
			return f"\n\n+ {self.challenger.history.name} has been added to the top10 list, begining on the 10th spot."
		if self.defender is self.winner:
			return f"\n\n+ {self.defender.history.name} has {self.flawless}defended the {self.defender.rank_ordinal} spot!"
		else:
			return f"\n\n+ {self.challenger.history.name} has {self.flawless}took over the {self.defender.rank_ordinal} spot!" 
		
	@cached_property
	def str_version_or_no_score(self):
		if self.games_total:
			return f"\n\nGames were played in {self.version}"
		else:
			return "\n\nNo wins or loses have been scored."
		
	@cached_property
	def replays_folder_name(self):
		return f"Challenge{self.index}_{self.challenger.history.key} vs {self.defender.history.key}, {self.challenger.wins}-{self.defender.wins}, {self.version}"
		
	def __repr__(self):
		return f"|Cha{self.index}|{self.version}|{self.winner}{self.winner.wins}|{self.loser}{self.loser.wins}|"

	def __str__(self):
		return f"\n------------------------------------\n{self.replays_folder_name}\n```diff\n\n- Challenge № {self.index}\n- Update {self.dateString}{self.str_challenge_or_none}\n{self.str_score1v1_or_none}{self.str_score2v2_or_none}{self.str_add_and_kick_or_none}{self.str_defended_or_took_over}{self.custom_msg}{self.str_version_or_no_score}\n\nLet the challenges continue!\n\n{self.top10}```"








#-------------------------------------------------------------------------------------------------------------#
#"""---------------------------------------PlayerInChallenge.Class.03--------------------------------------"""#
#-------------------------------------------------------------------------------------------------------------#
class PlayerInChallenge:
	def __init__(self, master, key, wins1v1, wins2v2):
		self.key = key
		self.master = master
		self.wins1v1 = wins1v1
		self.wins2v2 = wins2v2
		self.wins = wins1v1 + wins2v2
		self.history = self.master.chasys.PLAYERS[key]
		self.history.challenges.append(master)
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
	def last_challenge(self):
		return self.history.challenges[-2]
	
	@cached_property
	def days_since_last_chall(self):	
		if self.last_challenge is None:
			return None # self.history.fecha_de_alta.date
		else:
			delta = self.master.date - self.last_challenge.date
			return delta.days # /30
		
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
		self.CHALLENGES = { index: Challenge(self, index, row) for index, row  in self.data.iterrows() }
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
		data.to_csv(
			path_or_buf = self.chacsv, 
			sep = ";", 
			index = True,
			decimal = ",", 
			encoding = "latin1"
		)
		print(".csv guardado.")

	def __write_chalog(self):
		super_string = f"##AutoGenerated by 'ChallengeSystem' {datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\nRegards, Bambi\n\n"
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
		cabeceras = ['chall','version','p1','p1wins1v1','p1wins2v2','p2','p2wins1v1','p2wins2v2','date']
		indice = 'chall'
		if self.chacsv.exists() and self.chacsv.stat().st_size >0 :
			data = pd.read_csv(
				filepath_or_buffer = self.chacsv, 
				sep = ";", 
				# decimal = ",", 
				encoding = "latin1",
				index_col = indice,
				dtype={'version': str}
			)
			# data.set_index(INDICE, inplace=True)
		else:
			data = pd.DataFrame(columns=cabeceras)
			data.set_index(INDICE, inplace=True)
			
		data.sort_index(inplace=True, ascending=True)
		# data.sort_values(by='chall', inplace=True)
		# data.sort_index(inplace=True)
		data = data.map(lambda x: x.strip() if isinstance(x, str) else x)
		data['message'] = data['message'].fillna('')
		# data['message'].fillna('', inplace=True)
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
	