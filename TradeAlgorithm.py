#
# Script that analyzes mutually beneficial fantasy football trades for your team. 
#
# Inputs:
#   teams.json - Players on each team in ESPN fantasy league. Replace LEAGUE_ID with your ESPN leagues ID (ex: https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leagues/{LEAGUE_ID}?view=mRoster&view=mTeam)
#   values.html - Saved webpage from fantasy pros website (ex: https://www.fantasypros.com/2019/10/week-5-fantasy-football-trade-value-chart-2019/)
#   myKey - Team alias on ESPN
#
# Outputs:
#   Prints out the best trades for your team (myKey)
#
# How it works:
#   Find the 'trade values' for each of the players in your (half PPR) league
#   Attempts all possible trades with each team (up to 2 players for 2 players)
#   Calculates the starters' (in standard lineup) values before and after the trade
#   Prints out the trade if both teams get better

import json
import codecs
from bs4 import BeautifulSoup

increaseNeededMe = 8
increaseNeededOp = 2
myKey = 'OLSO'

#
# Function to get starters' values from a team roster
#
def GetTeamValue(roster):
    qb = 0
    rb1 = 0
    rb2 = 0
    wr1 = 0
    wr2 = 0
    te = 0
    for player in roster:
        if int(player[2]) > qb and player[1] == "QB":
            qb = int(player[2])
        elif int(player[2]) > rb1 and player[1] == "RB":
            rb2 = rb1
            rb1 = int(player[2])
        elif int(player[2]) > rb2 and player[1] == "RB":
            rb2 = int(player[2])
        elif int(player[2]) > wr1 and player[1] == "WR":
            wr2 = wr1
            wr1 = int(player[2])
        elif int(player[2]) > wr2 and player[1] == "WR":
            wr2 = int(player[2])
        elif int(player[2]) > te and player[1] == "TE":
            te = int(player[2])
    total = qb + rb1 + rb2 + wr1 + wr2 + te
    return total

#
# Get the ESPN rosters from teams.json
#
rosters = {}
with open('teams.json') as json_file:
    data = json.load(json_file)
    for team in data['teams']:
        abbrev = team['abbrev']
        players = []
        for player in team['roster']['entries']:
            playerName = player['playerPoolEntry']['player']['fullName'].lower()
            playerName = playerName.split()[0] + " " + playerName.split()[1]
            playerName = playerName.replace('.','')
            playerName = playerName.replace('\'','')
            playerName = playerName.replace('’','')
            playerWithPosValue = (playerName, "", 0)
            players.append(playerWithPosValue)
        rosters[abbrev] = players
# print(rosters)

#
# Store trade value and position fantasy pros data from values.html
#
f = codecs.open("values.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), "lxml")
tables = soup.find_all('table')

players = {}
# QB
for i in range(2, len(tables[0].find_all('tr'))):
    name = tables[0].find_all('tr')[i].find_all('td')[0].string
    value = tables[0].find_all('tr')[i].find_all('td')[1].string
    players[name.lower()] = ("QB", value)

# RB (1), WR (2), TE (3)
positions = ["RB", "WR", "TE"]
for i, pos in enumerate(positions):
    for j in range(2, len(tables[i+1].find_all('tr'))):
        name = tables[i+1].find_all('tr')[j].find_all('td')[0].string
        name = name.split()[0] + " " + name.split()[1]
        name = name.replace('.','')
        name = name.replace('\'','')
        name = name.replace('’','')
        value = tables[i+1].find_all('tr')[j].find_all('td')[4].string
        players[name.lower()] = (pos, value)
# print(players.keys())

#
# Combine ESPN rosters and position/value data 
#
for rosterKey in rosters.keys():
    newRoster = []
    for player in rosters[rosterKey]:
        if player[0] in players.keys():
            updatedPlayer = (player[0], players[player[0]][0], players[player[0]][1])
            newRoster.append(updatedPlayer)
            del players[player[0]]

    rosters[rosterKey] = newRoster

print(players) # Print the players that remain from fantasy pros. These players have value and are not picked up.
print(rosters) # Print rosters (with players, positions, and values)

#
# For fun, print the total value of each team (starters + bench)
#
for rosterKey in rosters.keys():
    value = 0
    for player in rosters[rosterKey]:
        value += int(player[2])
    print(rosterKey + " " + str(value))

#
# Print and store the value of the starters for each team (before trades)
#
currTeamValues = {}
for key in rosters.keys():
    currTeamValues[key] = GetTeamValue(rosters[key])
    print(key + " " + str(currTeamValues[key]))


#
# Analyze all potential trades
# How it works: Switch players, calculate new starters scores, print trade if both teams increase by increaseNeededBy_
#

# 1 player for 1 player
for myIndex, myPlayer in enumerate(rosters[myKey]):
    for opKey in rosters.keys():
        if opKey == myKey:
            continue
        
        for opIndex, opPlayer in enumerate(rosters[opKey]):
            # Put my player on their team
            # Remove my player from my team
            # add opPlayer to myTeam
            # Remove opPlayer from their team

            opRoster = [myPlayer] + rosters[opKey][:opIndex] + rosters[opKey][opIndex+1:]
            myRoster = [opPlayer] + rosters[myKey][:myIndex] + rosters[myKey][myIndex+1:]
            
            opNewScore = GetTeamValue(opRoster)
            myNewScore = GetTeamValue(myRoster)

            if myNewScore > currTeamValues[myKey]+increaseNeededMe and opNewScore > currTeamValues[opKey] + increaseNeededOp:
                print(myKey + "(" + str(currTeamValues[myKey]) + "-->" + str(myNewScore) + ")" + " trade " + myPlayer[0] + " to " + opKey + "(" + str(currTeamValues[opKey]) + "-->" + str(opNewScore) + ")" + " for " + opPlayer[0])

# 2-2 trades
for myIndex1 in range(0, len(rosters[myKey]) - 1):
    myPlayer1 = rosters[myKey][myIndex1]
    for myIndex2 in range(myIndex1+1, len(rosters[myKey])):
        myPlayer2 = rosters[myKey][myIndex2]

        for opKey in rosters.keys():
            if opKey == myKey:
                continue
            for opIndex1 in range(0, len(rosters[opKey])-1):
                opPlayer1 = rosters[opKey][opIndex1]
                for opIndex2 in range(opIndex1+1, len(rosters[opKey])):
                    opPlayer2 = rosters[opKey][opIndex2]

                    opRoster = [myPlayer1, myPlayer2] + rosters[opKey][:opIndex1] + rosters[opKey][opIndex1+1:opIndex2] + rosters[opKey][opIndex2+1:]
                    myRoster = [opPlayer1, opPlayer2] + rosters[myKey][:myIndex1] + rosters[myKey][myIndex1+1:myIndex2] + rosters[myKey][myIndex2+1:]
            
                    opNewScore = GetTeamValue(opRoster)
                    myNewScore = GetTeamValue(myRoster)

                    if myNewScore > currTeamValues[myKey]+increaseNeededMe and opNewScore > currTeamValues[opKey] + increaseNeededOp:
                        print(myKey + "(" + str(currTeamValues[myKey]) + "-->" + str(myNewScore) + ")" + " trade " + myPlayer1[0] + "+" + myPlayer2[0] + " to " + opKey + "(" + str(currTeamValues[opKey]) + "-->" + str(opNewScore) + ")" + " for " + opPlayer1[0]+ "+" + opPlayer2[0])

# 2-1 trades
for myIndex1 in range(0, len(rosters[myKey]) - 1):
    myPlayer1 = rosters[myKey][myIndex1]
    for myIndex2 in range(myIndex1+1, len(rosters[myKey])):
        myPlayer2 = rosters[myKey][myIndex2]

        for opKey in rosters.keys():
            if opKey == myKey:
                continue
            for opIndex, opPlayer in enumerate(rosters[opKey]):

                opRoster = [myPlayer1, myPlayer2] + rosters[opKey][:opIndex] + rosters[opKey][opIndex+1:]
                myRoster = [opPlayer] + rosters[myKey][:myIndex1] + rosters[myKey][myIndex1+1:myIndex2] + rosters[myKey][myIndex2+1:]

                opNewScore = GetTeamValue(opRoster)
                myNewScore = GetTeamValue(myRoster)

                if myNewScore > currTeamValues[myKey]+increaseNeededMe and opNewScore > currTeamValues[opKey] + increaseNeededOp:
                    print(myKey + "(" + str(currTeamValues[myKey]) + "-->" + str(myNewScore) + ")" + " trade " + myPlayer1[0] + "+" + myPlayer2[0] + " to " + opKey + "(" + str(currTeamValues[opKey]) + "-->" + str(opNewScore) + ")" + " for " + opPlayer[0])

# 1-2 trades
for myIndex, myPlayer in enumerate(rosters[myKey]):
    for opKey in rosters.keys():
        if opKey == myKey:
            continue
        for opIndex1 in range(0, len(rosters[opKey])-1):
            opPlayer1 = rosters[opKey][opIndex1]
            for opIndex2 in range(opIndex1+1, len(rosters[opKey])):
                opPlayer2 = rosters[opKey][opIndex2]

                myRoster = [opPlayer1, opPlayer2] + rosters[myKey][:myIndex] + rosters[myKey][myIndex+1:]
                opRoster = [myPlayer] + rosters[opKey][:opIndex1] + rosters[opKey][opIndex1+1:opIndex2] + rosters[opKey][opIndex2+1:]

                opNewScore = GetTeamValue(opRoster)
                myNewScore = GetTeamValue(myRoster)

                if myNewScore > currTeamValues[myKey]+increaseNeededMe and opNewScore > currTeamValues[opKey] + increaseNeededOp:
                    print(myKey + "(" + str(currTeamValues[myKey]) + "-->" + str(myNewScore) + ")" + " trade " + myPlayer[0] + " to " + opKey + "(" + str(currTeamValues[opKey]) + "-->" + str(opNewScore) + ")" + " for " + opPlayer1[0]+ "+" + opPlayer2[0])