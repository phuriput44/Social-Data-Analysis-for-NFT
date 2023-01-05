import pandas as pd
import sklearn
import pymongo
import pickle
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

client = pymongo.MongoClient(
    "mongodb+srv://phuriput44:m4a1m4a1@seniorproject1.dell3sq.mongodb.net/?retryWrites=true&w=majority")
tweet = client["Tweet"]
coinlist = tweet.list_collection_names()
coin = client['SeniorProj']


def model(stocks_df,tweets_df):
    prelim = pd.merge(stocks_df, tweets_df, on='date')
    prelim = prelim.drop(columns = ["_id_x","_id_y","date","marketcap","tweets"])
    prelim.dropna(inplace=True)
    if len(tweets_df.index) <= 3 :
        return "Tweets too low to predict"
    features_prelim = prelim[:len(prelim)-1]
    labels_prelim = prelim["price"]
    if len(labels_prelim) > 1 :
        labels_prelim = labels_prelim[1:]

    X_train, X_test, y_train, y_test = train_test_split(features_prelim, labels_prelim, test_size=0.25, random_state=78)
    reg = sklearn.linear_model.LinearRegression()
    reg.fit(X_train, y_train)
    return reg.predict(features_prelim[-1:])

#pickle.dump(reg, open("model_LR.pkl", 'wb'))