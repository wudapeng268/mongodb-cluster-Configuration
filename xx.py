#encoding=UTF-8
#!usr/bin/pythonx
import datetime    
ISOTIMEFORMAT = '%Y-%m-%d %X'    
from pymongo import MongoClient
conn = MongoClient("外网 ip 1",53001)
db = conn.testsharding
    
def dateDiffInSeconds(date1,date2):
    timedelta = date2 - date1
    return timedelta.days*24*3600 +timedelta.seconds
db.testshardtable.drop()
date1 = datetime.datetime.now()
for i  in range(0,1000000): db.testshardtable.insert({"name":"ljai","age":i,"addr":"fuzhou"})
c = db.testshardtable.find().count()
print("count is ",c)
date2 = datetime.datetime.now()
print(date1)
print(date2)
print("消耗：",dateDiffInSeconds(date1,date2),"seconds")
conn.close()