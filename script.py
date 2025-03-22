from pymongo import *
import datetime
import bson
import flask as fl
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField


#connect to the database
client = MongoClient(host='localhost', port=27017)
db = client["fine-tree"]
packs = db["packs"]
playlists = db["playlists"]
quizzes = db["quizzes"]
records = db["records"]
units = db["units"]



def getType(id: bson.ObjectId) -> str:
    if packs.find_one({"_id": id}):
        return "pack"
    elif playlists.find_one({"_id": id}):
        return "playlist"
    elif units.find_one({"_id": id}):
        return "unit"
    elif quizzes.find_one({"_id": id}):
        return "quiz"
    elif records.find_one({"_id": id}):
        return "record"
    else:
        return None

def getObj(id: bson.ObjectId) -> object:
    type = getType(id)
    if type == "pack":
        return Pack.fromDict(packs.find_one({"_id": id}))
    elif type == "playlist":
        return Playlist.fromDict(playlists.find_one({"_id": id}))
    elif type == "unit":
        return Unit.fromDict(units.find_one({"_id": id}))
    elif type == "quiz":
        return Quiz.fromDict(quizzes.find_one({"_id": id}))
    elif type == "record":
        return Record.fromDict(records.find_one({"_id": id}))
    else:
        return None


class Playlist:
    def __init__(self, name: str, description: str, date: datetime.datetime, id: bson.ObjectId, items: list) -> None:
        self.name = name
        self.description = description
        self.date = date
        self.id = id
        self.items = items
    
    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "date": self.date,
            "id": self.id,
            "items": self.items
        }

    def fromDict(self, data: dict) -> None:
        try:
            self.name = data["name"]
            self.description = data["description"]
            self.date = data["date"]
            self.id = data["id"]
            self.items = data["items"]
        except KeyError:
            return None

    def getItems(self) -> list:
        item_data = list(quizzes.find({"_id": {"$in": self.items}}))
        return [Quiz.fromDict(i) for i in item_data]

class Pack:
    def __init__(self, name: str, description: str, date: datetime.datetime, id: bson.ObjectId) -> None:
        self.name = name
        self.description = description
        self.date = date
        self.id = id

    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "date": self.date,
            "id": self.id
        }

    def fromDict(self, data: dict) -> None:
        self.name = data["name"]
        self.description = data["description"]
        self.date = data["date"]
        self.id = data["id"]
    
    def getUnits(self) -> list:
        unit_data = list(units.find({"pack_id": self.id}))
        return [Unit.fromDict(i) for i in unit_data]
    
    def getQuizzes(self) -> list:
        unitList = self.getUnits()
        if unitList == []:
            return []
        else:
            quizList = []
            for i in unitList:
                quizList += list(quizzes.find({"unit_id": i["id"]}))
            return [Quiz.fromDict(i) for i in quizList]
    
    def getTree(self) -> list:
        unitList = self.getUnits()
        if unitList == []:
            return []
        else:
            tree = []
            for i in unitList:
                tree.append({
                    "unit": i,
                    "quizzes": [Quiz.fromDict(j) for j in list(quizzes.find({"unit_id": i["id"]}))]
                })
            return tree
        
    def getRecords(self) -> list:
        recordList = []
        for i in self.getQuizzes():
            recordList += list([Quiz.fromDict(i) for i in records.find({"quiz_id": i["id"]})])
        return [Record.fromDict(i) for i in recordList] if recordList else None


class Unit:
    def __init__(self, name: str, description: str, pack_id: bson.ObjectId, id: bson.ObjectId) -> None:
        self.name = name
        self.description = description
        self.pack_id = pack_id
        self.id = id

    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "pack_id": self.pack_id,
            "id": self.id
        }

    def fromDict(self, data: dict) -> None:
        try:
            self.name = data["name"]
            self.description = data["description"]
            self.pack_id = data["pack_id"]
            self.id = data["id"]
        except KeyError:
            return None

    def getQuizzes(self) -> list:
        return list(quizzes.find({"unit_id": self.id}))

    def getPack(self) -> dict:
        pack_data = packs.find_one({"_id": self.pack_id})
        return Pack.frommDict(pack_data) if pack_data else None
    
    def getRecords(self) -> list:
        record_data = []
        for i in self.getQuizzes():
            record_data += list(records.find({"quiz_id": i["id"]}))
        return [Record.fromDict(i) for i in record_data] if record_data else None


class Quiz:
    def __init__(self, question: str, answer: str, unit_id: bson.ObjectId, id: bson.ObjectId, hint: str, type: str, meta: dict) -> None:
        self.question = question
        self.answer = answer
        self.unit_id = unit_id
        self.id = id
        self.hint = hint
        self.type = type
        self.meta = meta
    
    def __dict__(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "unit_id": self.unit_id,
            "id": self.id,
            "hint": self.hint,
            "type": self.type,
            "meta": self.meta
        }
    
    def fromDict(self, data: dict) -> None:
        try:
            self.question = data["question"]
            self.answer = data["answer"]
            self.unit_id = data["unit_id"]
            self.id = data["id"]
            self.hint = data["hint"]
            self.type = data["type"]
            self.meta = data["meta"]
        except KeyError:
            return None
    
    def getUnit(self) -> 'Unit':
        unit_data = units.find_one({"_id": self.unit_id})
        return Unit.fromDict(units.find_one({"_id": self.unit_id})) if unit_data else None
    
    def getRecords(self) -> list:
        record_data = list(records.find({"quiz_id": self.id}))
        return [Record.fromDict(i) for i in record_data] if record_data else None


class Record:
    def __init__(self, quiz_id: bson.ObjectId, state: int, date: datetime.datetime, id: bson.ObjectId) -> None:
        self.quiz_id = quiz_id
        self.state = state
        self.date = date
        self.id = id
    
    def __dict__(self) -> dict:
        return {
            "quiz_id": self.quiz_id,
            "correct": self.correct,
            "date": self.date,
            "id": self.id
        }
    
    def fromDict(self, data: dict) -> None:
        try:
            self.quiz_id = data["quiz_id"]
            self.state = data["state"]
            self.date = data["date"]
            self.id = data["id"]
        except KeyError:
            return None
    
    def getQuiz(self) -> Quiz:
        quiz_data = quizzes.find_one({"_id": self.quiz_id})
        return Quiz.fromDict(quiz_data) if quiz_data else None



app = fl.Flask(__name__)


@app.route("/")
def showIndex():
    return fl.render_template("index.html")

@app.route("/req/<prosess>/<target>/<arg>")
def prosessReq(prosess, target, arg):
    if prosess == "create":
        pass
    elif prosess == "read":
        obj = getObj(bson.ObjectId(target))
        if obj == None:
            return "404"
        else:
            if arg == "*" or arg == "all":
                return obj.__dict__()
            else:
                return obj.__dict__()[arg]
    elif prosess == "delete":
        pass
    elif prosess == "update":
        pass


@app.route("/create/<type>")
def create(type):
    if type == "playlist":
        pass
    elif type == "pack":
        pass
    elif type == "unit":
        pass
    elif type == "quiz":
        pass
    elif type == "record":
        pass
    else:
        return "404"

@app.route("/edit")
def edit(id):
    obj = getObj(bson.ObjectId(id))
    type = getType(bson.ObjectId(id))
    if obj == None:
        return "404"
    elif type == "playlist":
        return fl.render_template("edit_playlist.html", playlist=obj)    
    elif type == "pack":
        return fl.render_template("edit_pack.html", pack=obj)
    elif type == "unit":
        return fl.render_template("edit_unit.html", unit=obj)
    elif type == "quiz":
        return fl.render_template("edit_quiz.html", quiz=obj) 
    elif type == "record":
        return fl.render_template("edit_record.html", record=obj)
    else:
        return "404"

#mainloop
if __name__ == "__main__":
    app.run(debug=True)