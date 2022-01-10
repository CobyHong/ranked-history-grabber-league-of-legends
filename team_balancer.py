import os
import sys
import requests
import json
import time
from bs4 import BeautifulSoup
import statistics

# USAGE: python team_balancer.py list_of_players.txt

# ==============================================================

# open file and read line by line for player names.
# information is stored and return in a dictionary.
# dictionary consisting of a count of total players and players.
def createPlayersFromFile(filename):
	player_names = []
	player_dic = {
		'total' : {},
		'players' : {}
	}

	try:
		with open(filename, 'r', encoding='utf-8') as file:
			for line in file:
				player = line.lstrip().rstrip()
				if player != '':
					player_names.append(player)

		count = 0
		for player in player_names:
			player_dic['players'][player] = {}
			count += 1
		player_dic['total']['count'] = count

		print('\n-------------------------------------------')
		print('Players found from text file:\n')
		print(json.dumps([player_dic], sort_keys=False, indent=4))
		print('\n-------------------------------------------\n')
		return player_dic
	except:
		print('\nError:	could not parse file.')
		print('			please ensure file follows correct format of')
		print('			one player per line in txt file.\n')
		os._exit(0)
	return 0

# ==============================================================

# fetches the ranks for each plaayer and sets their current rank.
# calls endpoint to op.gg, pares html to get ranks from previous seasons.
# some logic to handle higher ranked players that no longer have tiers markings.
# stores in dictionary as list of dicts. each dict being that season's ranked info.
def fetchPlayers(dictionary):
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
	
	print('Rank fetching for players starting...\n')
	for player in dictionary['players']:
		mmr = None
		print('Fetching rank history from user: %s\n' % (str(player)))
		# needs multiple tries sometimes to fetch.
		# for i in range(0,3):
		mmr = requests.get('https://na.op.gg/summoner/userName=%s' % (str(player)), headers=headers)

		# request returned as html. use parser to find where ranks are.
		soup = BeautifulSoup(mmr.text, "html.parser")
		past_rank_list = soup.find_all("li", {"class": "Item tip"})

		# list for current player.
		ranks = []
		
		# accumulate current player's rank history.
		for season in past_rank_list:
			curr_season_rank_list = season['title'].split(' ')

			ranking = curr_season_rank_list[0].rstrip().lstrip().upper()
			tier = None
			lp = None

			# logic below deals with higher ranked players who do not have tier markings.
			if (ranking != 'MASTER') and (ranking != 'GRANDMASTER') and (ranking != "CHALLENGER"):
				tier = int(curr_season_rank_list[1].rstrip().lstrip())
				if len(curr_season_rank_list) == 2:
					lp = 0
				else:
					lp = int(curr_season_rank_list[2].rstrip().lstrip().replace('LP', ''))
			else:
				tier = 0
				lp = int(curr_season_rank_list[1].rstrip().lstrip().replace('LP', ''))

			# add the parsed rank to current players ranked list.
			ranks.append(
				{
					'rank' : ranking,
					'tier' : tier,
					'lp' : lp
				}
			)

		print(json.dumps(ranks, sort_keys=False, indent=4))
		# append ranks to current player.
		dictionary['players'][player]['ranks'] = ranks
		dictionary['players'][player]['current_rank'] = ranks[-1]

	print('\nRank fetching for players complete.')
	print('\n-------------------------------------------\n')
	return 0

# ==============================================================

# goes through each player
# goes through that player's season ranks.
# calculates a median score based on rank history.
# median chosen as score if lower than current rank score.
def getAverageRankForPlayer(dictionary):
	rankings = {
		'IRON': 0,
		'BRONZE': 1,
		'SILVER': 2,
		'GOLD': 3,
		'PLATINUM': 4,
		'DIAMOND': 5,
		'MASTER': 6,
		'GRANDMASTER': 7,
		'CHALLENGER': 8
	}

	# is reversed as a point system.
	tiers = {
		0 : 0,
		1 : 0.75,
		2 : 0.50,
		3 : 0.25,
		4 : 0,
		5 : 0
	}

	print('Rank score median calculations for players starting...\n')
	for player in dictionary['players']:
		scores = []
		chosen_medium = None
		score_basis = ''

		print('Fetching rank score median for user: %s' % (str(player)))

		# getting medium ranking score.
		for season_rank in dictionary['players'][player]['ranks']:
			whole = rankings[season_rank['rank']]
			dec = tiers[season_rank['tier']]
			score = whole + dec
			scores.append(score)
		median_rank = statistics.median(scores)

		# getting current ranking score.
		whole = rankings[dictionary['players'][player]['current_rank']['rank']]
		dec = tiers[dictionary['players'][player]['current_rank']['tier']]
		current_rank = whole + dec

		# if current rank higher than medium, use current rank as score.
		if current_rank > median_rank:
			chosen_medium = current_rank
			score_basis = 'current rank'
		else:
			chosen_medium = median_rank
			score_basis = 'median rank'

		print('Calculated score for: %s\n' %(chosen_medium))
		dictionary['players'][player]['rank_score'] = {
			'score' : chosen_medium,
			'scoring_basis' : score_basis
		}

	print('\nRank score median calculations for players complete.')
	print('\n-------------------------------------------\n')

	# getting the medium for all scores.
	print('Total medium rank score calculations starting...\n')
	total_scores = []
	for player in dictionary['players']:
		total_scores.append(dictionary['players'][player]['rank_score']['score'])
	median_total_rank = statistics.median(total_scores)
	dictionary['total']['median_score'] = median_total_rank
	print('\nTotal medium rank score calculations complete')
	print('\n-------------------------------------------\n')

	return 0

# ==============================================================

# just writes out the dictionary into a json file.
# json file gets put in whatever directory the script currently is in.
def dictionaryToJson(dic, name):

	print('Writing player ranks dictionary to file...\n')
	with open(name + ".json", "w") as outfile:
		json.dump(dic, outfile, indent=4, sort_keys=True)
	print('Saved to file: %s' % (name + '.json'))
	print('\nWriting player ranks dictionary to file complete.')
	print('\n-------------------------------------------\n')
	return 0

# ==============================================================

def main():
	dictionary = createPlayersFromFile(sys.argv[1])

	fetchPlayers(dictionary)

	getAverageRankForPlayer(dictionary)

	dictionaryToJson(dictionary, 'coby_output')

	return 0

# ==============================================================

if __name__ == '__main__':
    sys.exit(main()) 

# ==============================================================