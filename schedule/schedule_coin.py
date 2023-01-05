import pymongo
import pandas as pd
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
import time
import tweepy
from nltk.tokenize import word_tokenize
import re
import LR_predict
import schedule
import pickle
from requests_oauthlib import OAuth1Session

client = pymongo.MongoClient(
    "mongodb+srv://phuriput44:m4a1m4a1@seniorproject1.dell3sq.mongodb.net/?retryWrites=true&w=majority")
db = client["SeniorProj"]
dic = client["dict"]
tweetdb = client["Tweet"]
pred = client["Predicting"]
col_list = db.list_collection_names()
coin = dic['coin']
coin_df = pd.DataFrame(list(coin.find()))
startDate = datetime.today() - timedelta(days=1)
cg = CoinGeckoAPI()

consumer_key = "Ge1Knvav47fKzAlVKZOsTciBf"
consumer_secret = "DB0kVFP7SEXatfjxzuF5oU6L6KBoONBeU5dbj7qWb5CgxLT1p7"
access_token = "884608372825137152-1GHCjPPI7SuBTQN9jcMwM89bDRTT3hq"
access_token_secret = "L8UKwlvPekNtPXTRA3WY5dhusoj9jNaGlDSimKSq8qOpd"

twitter = OAuth1Session(consumer_key,
                        client_secret=consumer_secret,
                        resource_owner_key=access_token,
                        resource_owner_secret=access_token_secret)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, retry_count=3)
model = pickle.load(open('model_sentiment.pkl', 'rb'))


def cleanTxt(text):
    text = re.sub(r'@[A-Za-z0-9]+', '', str(text))
    text = re.sub(r'#', '', str(text))
    text = re.sub(r'RT[\s]', '', str(text))
    text = re.sub(r'https?:\/\/S+', '', str(text))
    return text


def getAnalysis(score):
    if score >= 0:
        return "Positive"
    else:
        return "Negative"


def predict(name):
    re_client = pymongo.MongoClient(
        "mongodb+srv://phuriput44:m4a1m4a1@seniorproject1.dell3sq.mongodb.net/?retryWrites=true&w=majority")
    re_db = re_client["SeniorProj"]
    re_tweetdb = re_client["Tweet"]
    tweets_df = pd.DataFrame(list(re_tweetdb[name].find()))
    stocks_df = pd.DataFrame(list(re_db[name].find()))
    if len(tweets_df.index) <= 3 :
        return 
    predicted = LR_predict.model(tweets_df, stocks_df)

    pred[name].insert_one({
        "date": datetime.today().strftime("%d-%m-%Y"),
        "predicted": predicted[0]
    })


def sentiment_analysis(text):
    temp = pd.Series(text)
    tweets_tokenized = temp.apply(
        lambda x: word_tokenize(x) if not pd.isnull(x) else x)
    tweets_noiseless = tweets_tokenized.apply(
        lambda y: cleanTxt(y) if not pd.isnull([y]).any() else y)
    tweets_classified = tweets_noiseless.apply(lambda z: model.classify(
        dict([token, True] for token in z)) if not pd.isnull([z]).any() else z)
    return tweets_classified.mode().values[0]


def fetch():
    print("Start Fetching")
    for col in col_list:
        # Get Tweets ============================================================================
        temp = []
        print(col+" Start fetching tweets")
        tweets = tweepy.Cursor(api.search_tweets,
                               q=col+" " +
                               coin_df['symbol'][coin_df['name']
                                                 == col].values[0]+" since:"+str(startDate.date()),
                               lang="en",
                               tweet_mode='extended'
                               ).items()
        for tweet in tweets:
            if 'retweeted_status' in tweet._json:
                full_text = tweet._json['retweeted_status']['full_text']
            else:
                full_text = tweet.full_text
            full_text = cleanTxt(full_text)
            temp.append(full_text)
        if temp != []:
            sentiment = sentiment_analysis(temp)
            tweetdb[col].insert_one({
                "tweets": temp,
                "date": str(startDate.date().strftime("%d-%m-%Y")),
                "sentiment": int(sentiment)})
        # Get coin ====================================================================================
        print(col+" Start fetching price")
        history = cg.get_coin_history_by_id(
            coin_df['id'][coin_df['name'] == col].values[0], startDate.date().strftime("%d-%m-%Y"))
        if "market_data" in history:
            price = history["market_data"]["current_price"]["usd"]
            volume = history["market_data"]["total_volume"]["usd"]
            db[col].insert_one({
                "date": startDate.date().strftime("%d-%m-%Y"),
                "price": price,
                "marketcap": history["market_data"]["market_cap"]["usd"],
                "volume": volume
            })
            time.sleep(30)
            if temp != []:
                predict(col)
        print(col+" Done")
        time.sleep(100)


print("Start program")
fetch()
# schedule.every().day.at("00:00").do(fetch)
# while True:
#    schedule.run_pending()
