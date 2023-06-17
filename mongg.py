import urllib
import pymongo
from pymongo import MongoClient
import re,time,pandas as pd,numpy as np

 
database_user = urllib.parse.quote_plus('plgadmin1')
database_pass = urllib.parse.quote_plus('plg@2o2o&*(')
mongo_connection = MongoClient('mongodb://' + database_user + ':' + database_pass +'@34.251.243.79/?authMechanism=SCRAM-SHA-1&authSource=admin&retryWrites=true&w=majority')
db = mongo_connection['plg1']
print('started')


q = {'gender': {'$in': [re.compile('^Men', re.IGNORECASE)]}, 'website': {'$in': [re.compile('^vestiaire', re.IGNORECASE), re.compile('^lampoo', re.IGNORECASE), re.compile('^realreal', re.IGNORECASE), re.compile('^cudoni', re.IGNORECASE)]}, 'category': {'$in': [re.compile('^earrings', re.IGNORECASE)]}}

q={}

prices = db.accounts_productdata.aggregate([{"$match": q},
{"$group": {"_id": "null", \
    "max_price": {"$max": "$aggregate_price"},\
    "min_price": {"$min": "$aggregate_price"},\
    "avg_price": {"$avg": "$aggregate_price"},\
    "aggregate_sum":{"$sum":"$aggregate_price"}}}])

col_data={}

print()

for i in prices:
    print(i)
    col_data['max_price'] = (i['max_price'])
    col_data['min_price'] = (i['min_price'])
    col_data['avg_price'] = (i['avg_price'])
    col_data['aggregate_sum'] = (i['aggregate_sum'])





df = pd.read_excel('result2.xlsx')

for ind,rw in df.iterrows():
    sub_category = str(rw['sub_category']).strip().lower()
    gender = str(rw['gender']).strip().lower()
    Category = str(rw['category']).strip().lower()

    db.filter_pathway.insert_one({"gender":gender,"category":Category,"sub_category":sub_category})


mongo_connection.close()

quit()