# ChallengeSystem & BambiBot

data/challenges.csv

types of challenge: 
normal: used by a challenges fully completed, should be posted with the replay pack. when adding the row in the .csv, the order of the players dont matter. cha.py will figure out the roles of p1/p2 automatically. in the version label should be the patch name.
KICK_ADD_MODE: used when we want to delete a player from the list, pushing up everyone behind. but in the 10th spot we add a new player. added player must be loged as p1 and kickes as p2. must to write this kickandmode flag in the version column. 1v1/2v2 columns must be zero.
NO_SCORE_MODE: used when one player challenges another but he's dodged, or he's inactive, or refuses to defend his own spot. he simply loses the spot but we dont alter the winrates of any player. 1v1/2v2 columns must be cero. patch column must to be this flag. p1 must be the challenger and p2 must be the defender.



once .csv is updated, run cha.py to autoupdate the data/cha.log, which has the story of challenges. in the top of the file there will be the latest.


### Commands:
python cha.py -> updates the output/challenges.log and output/status.log
python cha.py 334 post -> post that chlng with its respective replays in chaupdates discord
python cha.py 334 post_all -> post that chlng, and each 8 minds, sends the subsequent ones.
