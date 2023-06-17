import urllib
import pymongo
from pymongo import MongoClient
import re,time,pandas as pd,numpy as np

 
database_user = urllib.parse.quote_plus('plgadmin1')
database_pass = urllib.parse.quote_plus('plg@2o2o&*(')
mongo_connection = MongoClient('mongodb://' + database_user + ':' + database_pass +'@34.251.243.79/?authMechanism=SCRAM-SHA-1&authSource=admin&retryWrites=true&w=majority')
db = mongo_connection['plg1']
print('started')


# col = db.accounts_productdata.find({})
# print((col.count()))


# db.getCollection("accounts_productdata").updateMany({"condition2":"Lining: visible stain. Main fabric: slightly visible pulled threads."},{$set :{"condition2":"fair conditon"}   })

# df = pd.read_excel(r'C:\Users\Dell\Downloads\competitor_item_condition_vs_rlvd.xlsx',sheet_name='WRT COND2')
# df = df.fillna('')

# for ind,rw in df.iterrows():
#     # if rw['NEW CONDITION IN DB'] not in ('',None,np.nan):
#     db.accounts_productdata.update_many(
#         {"website":{"$regex":rw['website'].strip(),'$options':'i'},
#         "condition2":rw['condition2'].strip()},
#         {'$set' :{"condition2":rw['NEW CONDITION IN DB'].strip()}})   

x = '''blanks
excellent condition
excellent condition with defects
fair conditon
good condition
never worn without tags (nwot)
new with tags (nwt)
very good condition 
very good/good condition'''
x = [i.strip() for i in x.split('\n')]

for i in x:
    db.configuration.insert_one({"name":i,"classification":"condition","percentage":None})

# df = pd.DataFrame(list(query))
# df.to_csv('op_cofnfig.csv')
