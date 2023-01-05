import pymongo
from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime
from bson.json_util import ObjectId
import json

client = pymongo.MongoClient(
    "mongodb+srv://phuriput44:m4a1m4a1@seniorproject1.dell3sq.mongodb.net/?retryWrites=true&w=majority")
db = client["SeniorProj"]
dic = client["dict"]
tweetdb = client["Tweet"]
pred = client["Predicting"]
coin = dic['coin']
col_list = db.list_collection_names()


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)

# กด Run แล้วเข้า path http://127.0.0.1:5000/getdata/(ชื่อเหรียญ) เพื่อดูตัวอย่างข้อมูล


app = Flask(__name__)
app.config.from_object(__name__)
app.json_encoder = MyEncoder
CORS(app, resources={r"/*": {'origins': "*"}})


@app.route('/', methods=['GET'])
def hello():
    return ("Hello world")


@app.route('/getTweets/<coin_name>', methods=['GET'])
def getTweets(coin_name):
    res = tweetdb[coin_name].find()
    return jsonify(list(res))


@app.route('/getPrices/<coin_name>', methods=['GET'])
def getPrices(coin_name):
    res = db[coin_name].find()
    return jsonify(list(res))


@app.route('/getCoins', methods=['GET'])
def getCoins():
    res = col_list
    return jsonify(list(res))


@app.route('/getPredict/<coin_name>', methods=['GET'])
def getPredict(coin_name):
    res = pred[coin_name].find()
    return jsonify(list(res))


@app.route('/getDetail/<coin_name>', methods=['GET'])
def getDetail(coin_name):
    get_coin = coin.find_one({'symbol': coin_name})
    coin_name = get_coin["name"]
    get_price = pd.DataFrame(list(db[coin_name].find()))
    get_price = get_price.drop(columns=["_id", "marketcap", "volume"])
    get_price_json = get_price.to_json(orient="records")
    get_tweets = pd.DataFrame(list(tweetdb[coin_name].find()))
    get_pred = pd.DataFrame(list(pred[coin_name].find()))
    if len(get_tweets.index) != 0:
        get_sentiment = get_tweets.drop(columns=["_id", "tweets"])
        get_sentiment = get_sentiment.to_json(orient="records")
    else:   
        get_sentiment = None
    
    if len(get_pred.index) != 0:
        get_pred = get_pred.drop(columns=["_id"])
        pred_out = "Up" if float(get_pred[-1:].predicted.values[0]) > float(get_price[-1:].price.values[0]) else "Down"
        percent = round(((float(get_pred[-1:].predicted.values[0]) - float(get_price[-1:].price.values[0]  ))/ float(get_price[-1:].price.values[0])) * 100,2)
    else:
        pred_out = "Unpredicted"
        percent = 0

    res = {
        "name": get_coin['name'], "symbol": get_coin['symbol'], "price": float(get_price[-1:].price.values[0]), "address": get_coin['address'], "chain": get_coin['platforms'],
        "cur_sentiment": int(get_tweets[-1:].sentiment.values[0]) if len(get_tweets.index) != 0 else None, "all_sentiment": get_sentiment,
        "all_price": get_price_json, "ath": float(get_coin['ath']), "atl": float(get_coin['atl']), "links": [{"link": "https://twitter.com/"+str(get_coin['twitter']),
                                                                                                              "type": "twitter"},
                                                                                                             {"link": get_coin['homepage'],
                                                                                                              "type": "homepage"}],
        "all_predict" : None if len(get_pred.index) == 0 else get_pred.to_json(orient="records") , "cur_predict" : {"date" : datetime.today().date().strftime("%d-%m-%Y"),
                                                                              "predict" :  { "status": pred_out,
                                                                                             "percent": percent}}
    }
    return res


@app.route('/getOverview/', methods=['GET'])
def getOverview():
    res = []
    for col in col_list:
        get_coin = coin.find_one({'name': col})
        get_price = pd.DataFrame(list(db[col].find()))
        get_price = get_price.drop(columns=["_id"])
        get_tweets = pd.DataFrame(list(tweetdb[col].find()))
        data = {
            "name": get_coin['name'], "symbol": get_coin['symbol'], "price": float(get_price[-1:].price.values[0]),
            "marketcap": float(get_price[-1:].marketcap.values[0]), "volume": float(get_price[-1:].volume.values[0]),
            "pic": get_coin['image'], "sentiment": int(get_tweets[-1:].sentiment.values[0]) if len(get_tweets.index) != 0 else 0,
        }
        res_data = {"name": col, "data": data}
        res.append(res_data)

    return res


@app.route('/getComment/<coin_name>', methods=['GET'])
def getComment(coin_name):
    get_coin = coin.find_one({'symbol': coin_name})
    coin_name = get_coin["name"]
    get_tweets = pd.DataFrame(list(tweetdb[coin_name].find()))
    get_tweets = get_tweets.drop(columns=["_id", "sentiment"])
    tweets = get_tweets[-1:].tweets.values[0]
    date = get_tweets[-1:].date.values[0]
    res = {
        "date": date,
        "tweets": tweets
    }
    return res


@app.route('/getAllComment/', methods=['GET'])
def getAllComment():
    res = []
    for col in col_list:
        get_tweets = pd.DataFrame(list(tweetdb[col].find()))
        if len(get_tweets.index) != 0:
            get_tweets = get_tweets.drop(columns=["_id", "sentiment"])
            tweets = get_tweets[-1:].tweets.values[0]
            date = get_tweets[-1:].date.values[0]
            data = {
                "date": date,
                "tweets": tweets
            }
        res.append(data)
    d = {}
    for item in res:
        d.setdefault(item['date'], []).append(item["tweets"])
    list(d.values())
    return d


@app.route('/getToCompare/<coin_name>', methods=['GET'])
def getToCompare(coin_name):
    get_coin = coin.find_one({'symbol': coin_name})
    coin_name = get_coin["name"]
    get_price = pd.DataFrame(list(db[coin_name].find()))
    get_price = get_price.drop(columns=["_id"])
    get_pred = pd.DataFrame(list(pred[coin_name].find()))
    if len(get_pred.index) != 0:
        get_pred = get_pred.drop(columns=["_id"])
        pred_out = "Up" if float(get_pred[-1:].predicted.values[0]) > float(get_price[-1:].price.values[0]) else "Down"
        percent = round(((float(get_pred[-1:].predicted.values[0]) - float(get_price[-1:].price.values[0]  ))/ float(get_price[-1:].price.values[0])) * 100,2)
    else:
        pred_out = "Unpredicted"
        percent = 0
    res = {
        "name": get_coin['name'], "symbol": get_coin['symbol'], "price": get_price[-1:].price.values[0],
        "marketcap": get_price[-1:].marketcap.values[0], "volume": get_price[-1:].volume.values[0],
        "pic": get_coin['image'], "total_supply": get_coin['total_supply'], "max_supply": get_coin['max_supply'],
        "predict": {"status" : pred_out,
                    "percent" : percent}
    }
    return res


if __name__ == "__main__":
    app.run(debug=True)
