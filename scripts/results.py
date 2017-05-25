from StringIO import StringIO
from pymongo import MongoClient
import pycurl
import argparse
import playerHandler
import goalieHandler
import csv
import datetime
from bson.json_util import dumps

#parsing db results for attribute of interest
def extract(key1, key2, val):
	before, key, after = str(val).partition(key1)
	before, key, after = after.partition(key2)
	return before

#check if points exist for player (if not, the player didn't play)
def checkPoints(points):
	if points=='':
		return 0
	else :
		return points

client = MongoClient()
db_gameStats=client.gameStats
db_teams=client.test
db_results=client.results
db_userResults=client.userResults

#get date in db friendly format (to be used as collection name)
# now = datetime.datetime.now().strftime("x%Y%m%d")
# date = datetime.datetime.now().strftime("%m/%d/%Y")

now = datetime.datetime.now().strftime("x20170523")
date = datetime.datetime.now().strftime("05/23/2017")

#file that will be outputted
file='../public/files/'+str(now)+'.csv'
siteFriendlyFile='/files/'+str(now)+'.csv'

#prepare csv file, write first line
out = csv.writer(open(file, "w"), delimiter=',', quoting=csv.QUOTE_NONE)
out.writerow(["Results For", date])

#get all players for that day
tempArray=[]
playerArray=[]

result=db_gameStats[now].find({})
for player in result:
	tempArray.append(dumps(player))

#extract fields
playerArray=[]
for i in range (0, len(tempArray)):
	playerArray.append([])
	playerArray[i].append(extract("name\": \"", "\"", tempArray[i]))
	playerArray[i].append(float(extract("fpoints\": ", ",", tempArray[i])))
	playerArray[i].append(extract("goals\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("assists\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("looseBalls\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("turnovers\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("causedTurnovers\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("saves\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("goalsAgainst\": \"", "\"", tempArray[i]))
	playerArray[i].append(extract("winLoss\": \"", "\"", tempArray[i]))
#sort based on user score
sortedPlayerArray= sorted(playerArray, key=lambda x: x[1], reverse=True)

#write to daily log file
out.writerow([])
out.writerow(["Player Results"])
out.writerow(["Player Name", "Fantasy Points", "Goals", "Assists", "Loose Balls", "Turnovers", "Caused Turnovers", "Saves", "Goals Against", "Goalie Win / Loss"])
out.writerow([])
for i in range (0, len(sortedPlayerArray)):
	out.writerow([sortedPlayerArray[i][0], sortedPlayerArray[i][1], sortedPlayerArray[i][2], sortedPlayerArray[i][3],
		sortedPlayerArray[i][4], sortedPlayerArray[i][5], sortedPlayerArray[i][6], sortedPlayerArray[i][7], sortedPlayerArray[i][8], sortedPlayerArray[i][9],])







#now dealing with user teams & results
teamArray=[]
teamPoints=0
resultsArray=[]


#get all teams for that day
cursor = db_teams.teams.find({"theDate": date})
for team in cursor:
	#print dumps(team)
	teamArray.append(dumps(team))

	
#get the score of each player for that day (using plyayer ID)
i=0
for team in teamArray:	
	resultsArray.append([])
	teamPoints=0
	
	#sum points generated by each player
	player1Score=(float(checkPoints(extract("fpoints\": ", ",", dumps(db_gameStats[now].find_one({"id": extract("player1\": \"", "\"", team)}))))))
	player2Score=(float(checkPoints(extract("fpoints\": ", ",", dumps(db_gameStats[now].find_one({"id": extract("player2\": \"", "\"", team)}))))))
	player3Score=(float(checkPoints(extract("fpoints\": ", ",", dumps(db_gameStats[now].find_one({"id": extract("player3\": \"", "\"", team)}))))))
	player4Score=(float(checkPoints(extract("fpoints\": ", ",", dumps(db_gameStats[now].find_one({"id": extract("player4\": \"", "\"", team)}))))))
	player5Score=(float(checkPoints(extract("fpoints\": ", ",", dumps(db_gameStats[now].find_one({"id": extract("player5\": \"", "\"", team)}))))))
	username=extract("username\": \"", "\"", team)
	resultsArray[i].append(username)
	teamPoints=player1Score+player2Score+player3Score+player4Score+player5Score
	#append each player score
	resultsArray[i].append(teamPoints)
	resultsArray[i].append(player1Score)
	resultsArray[i].append(player2Score)
	resultsArray[i].append(player3Score)
	resultsArray[i].append(player4Score)
	resultsArray[i].append(player5Score)
	#append each player name to array
	resultsArray[i].append(extract("name\": \"", "\"", (dumps(db_teams.playerList.find_one({"id": extract("player1\": \"", "\"", team)})))))
	resultsArray[i].append(extract("name\": \"", "\"", (dumps(db_teams.playerList.find_one({"id": extract("player2\": \"", "\"", team)})))))
	resultsArray[i].append(extract("name\": \"", "\"", (dumps(db_teams.playerList.find_one({"id": extract("player3\": \"", "\"", team)})))))
	resultsArray[i].append(extract("name\": \"", "\"", (dumps(db_teams.playerList.find_one({"id": extract("player4\": \"", "\"", team)})))))
	resultsArray[i].append(extract("name\": \"", "\"", (dumps(db_teams.playerList.find_one({"id": extract("player5\": \"", "\"", team)})))))
	i+=1

#sort based on user score
resultsArray= sorted(resultsArray, key=lambda x: x[1], reverse=True)

#assign rank
i=0
rank=1
for i in range (0, len(resultsArray)):
	#check for a tie
	if i != 0:
		#there was a tie
		if resultsArray[i][1]==resultsArray[i-1][1]:
			resultsArray[i].append(str(resultsArray[i-1][12]))
			rank +=1

		#no tie
		else:
			resultsArray[i].append(rank)
			rank +=1
	else:
		resultsArray[i].append(rank)
		rank +=1

#update userResult db
for i in range (0, len(resultsArray)):
	result=db_userResults[resultsArray[i][0]].insert({
		"date":date,
		"fpoints":str(resultsArray[i][1]),
		"player1":str(resultsArray[i][7]),
		"player1Score":str(resultsArray[i][2]),
		"player2":str(resultsArray[i][8]),
		"player2Score":str(resultsArray[i][3]),
		"player3":str(resultsArray[i][9]),
		"player3Score":str(resultsArray[i][4]),
		"player4":str(resultsArray[i][10]),
		"player4Score":str(resultsArray[i][5]),
		"player5":str(resultsArray[i][11]),
		"player5Score":str(resultsArray[i][6]),
		"rank":str(resultsArray[i][12]),
		"totalEntrants":str(len(resultsArray)),
		"winningUser":str(resultsArray[0][0]),
		"winningScore":str(resultsArray[0][1]),
		"dlink":""+str(siteFriendlyFile)
		})


#write user results to daily log file
out.writerow([])
out.writerow([])
out.writerow(["User Results"])
out.writerow([])
out.writerow(["Rank", "Score", "Username", "","", "Team"])
for i in range (0, len(resultsArray)):
	out.writerow([resultsArray[i][12],resultsArray[i][1], resultsArray[i][0], 
		resultsArray[i][7], resultsArray[i][8], resultsArray[i][9], resultsArray[i][10],
		resultsArray[i][11]])










