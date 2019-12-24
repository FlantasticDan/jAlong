import json
import requests
import bs4
from flask import Flask, request
from flask_restful import Resource, Api

class JeopardyGame():
    def __init__(self, month, day, year):
        gameDate = "{}-{}-{}".format(year, month, day)
        jArchive_Query = r"http://www.j-archive.com/search.php?search=date%3A" + gameDate
        self.jArchive_Board_URL = requests.get(jArchive_Query).url
        gameID = self.jArchive_Board_URL.split('game_id=')[1]
        self.jArchive_Responses_URL = r"http://www.j-archive.com/showgameresponses.php?game_id=" + gameID

        # print("\nJ Archive URLs:")
        # print(self.jArchive_Board_URL)
        # print(self.jArchive_Responses_URL)

        self.parseGame()
    
    def parseGame(self):
        boardPage = requests.get(self.jArchive_Board_URL)
        responsePage = requests.get(self.jArchive_Responses_URL)

        boardParser = bs4.BeautifulSoup(boardPage.content, 'html.parser')
        responseParser = bs4.BeautifulSoup(responsePage.content, 'html.parser')

        self.j = JeopardyRound(boardParser.find(id='jeopardy_round'))
        self.j.parseAnswers(responseParser.find(id='jeopardy_round'))
        # self.j.printRound()

        self.dj = JeopardyRound(boardParser.find(id='double_jeopardy_round'))
        self.dj.parseAnswers(responseParser.find(id='double_jeopardy_round'))
        # self.dj.printRound()

        self.fj = FinalJeopardy(boardParser.find(id='final_jeopardy_round'))
        self.fj.addAnswer(responseParser.find(id='final_jeopardy_round'))
        # self.fj.printRound()
    
    def jsonify(self):
        jsonData = {
            'jeopardy': self.j.jsonify(),
            'double jeopardy': self.dj.jsonify(),
            'final jeopardy': self.fj.jsonify()
        }
        return jsonData


class FinalJeopardy:
    def __init__(self, roundSoup):
        # clueSoup = roundSoup.find_all('td', class_='clue')
        self.category = roundSoup.find(class_='category_name').text
        self.clue = roundSoup.find(class_= "clue_text").text
    
    def addAnswer(self, answerSoup):
        self.answer = answerSoup.find(class_='correct_response').text
    
    def printRound(self):
        print()
        print(self.category)
        print(self.clue)
        print(self.answer)
    
    def jsonify(self):
        jsonData = {
            'category': self.category,
            'clue': self.clue,
            'answer': self.answer
        }
        return jsonData
     
class JeopardyRound():
    def __init__(self, roundSoup):
        # Identify the Categories
        categorySoup = roundSoup.find_all('td', class_='category_name')
        self.categories = []
        # print('\nCategories:')
        for cat in categorySoup:
            self.categories.append(cat.text)
            # print(cat.text.title())
        
        # Pull Clues
        col = 0
        clueSoup = roundSoup.find_all('td', class_='clue')
        self.clues = []
        for clue in clueSoup:
            self.clues.append(JeopardyClue(clue, self.categories[col]))
            col += 1
            if col > 5:
                col = 0
    
    def parseAnswers(self, answerSoup):
        for i, answer in enumerate(answerSoup.find_all('td', class_='clue')):
            self.clues[i].addAnswer(answer)
    
    def printRound(self):
        for question in self.clues:
            print("")
            print(question.category)
            print(question.value)
            print(question.clue)
            print(question.answer)
            print(question.order)
    
    def jsonify(self):
        jsonData = []
        for clue in self.clues:
            clueDict = {
                'category': clue.category,
                'value': clue.value,
                'clue': clue.clue,
                'answer': clue.answer,
                'order': clue.order
            }
            jsonData.append(clueDict)
        return jsonData
        

class JeopardyClue():
    def __init__(self, clueSoup, category):
        # Identify Clue Text and Category
        try:
            self.clue = clueSoup.find(class_='clue_text').text
        except AttributeError:
            self.clue = "Unrevealed"
        self.category = category

        # Find Clue Value
        try:
            self.value = int(clueSoup.find(class_='clue_value').text[1:])
        except AttributeError:
            self.value = "Daily Double"
        
        # Find Order of Clue in Round
        try:
            self.order = int(clueSoup.find(class_='clue_order_number').text)
        except AttributeError:
            self.order = 100

    def addAnswer(self, answerSoup):
        try:
            self.answer = answerSoup.find(class_='correct_response').text
        except AttributeError:
            self.answer = "Mystery"

# JeopardyGame(12, 20, 2019)

## API ##
app = Flask(__name__)
api = Api(app)

class GetJeopardyGame(Resource):
    def get(self, month, day, year):
        game = JeopardyGame(month, day, year)

        return game.jsonify()

api.add_resource(GetJeopardyGame, '/game/<month>/<day>/<year>')


if __name__ == "__main__":
    app.run(port=888)