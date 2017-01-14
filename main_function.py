#-*- coding:utf-8 -*-
#!flask/bin/python
from flask import Flask, jsonify
from flask import abort
from flask import request
from numpy import *
import json
import demjson
import MySQLdb
from count import readFile1
from reliability_computing import static_Matching,func_1,func_2,func_3,judge_func_2,judge_func_3

# connect to databases
db = MySQLdb.connect("10.60.150.192","zhouwan","940828","thinkdevice")
cursor = db.cursor()

def sql_fetchall(sql):
    try: 
        cursor.execute(sql)
        db.commit()
        result = cursor.fetchall()
        return result
    except:
        print "Error:unable to fetch data"
        
def sql_zscg(sql):
    try:
        cursor.execute(sql)
        db.commit()
    except:
        db.rollback()

def update_benchmark(user_name,user_serialNumber,user_AndroidId,x):
    # delete old benchmark
    sql = "delete from benchmark_android2 where uname = '%s'"%user_name+\
    " and serialNumber = '%s'"%user_serialNumber+" and AndroidId = '%s'"%user_AndroidId 
    sql_zscg(sql)
        
    # add new benchmark
    sql = "INSERT INTO benchmark_android2 VALUES \
        ('%d','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%d')"\
        %(x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10],x[11],x[12],x[13],x[14],x[15],x[16],x[17],x[18],x[19])
    sql_zscg(sql)
    
def compute_reliability(inputData,new_dfp):
    num_input = len(inputData[0])
    # Dfp_Reliability = func_2(inputData,new_dfp,num_input)
    Dfp_Reliability = func_1(inputData,new_dfp,num_input)
    return Dfp_Reliability
   
# transform json file to tuple     
def read_json(input_dfp):
#    data = demjson.decode(input_dfp)
    data = input_dfp
    list = []  

    list.append(data['id'])
    list.append(data['uname'])
    list.append(data['androidid'])
    list.append(data['serialnumber'])
    list.append(data['mac'])
    list.append(data['timearea'])
    list.append(data['autolocktime'])
    list.append(data['getlocationmethod'])
    list.append(data['inputinfo'])
    list.append(data['fontlist'])
    list.append(data['phonebell'])
    list.append(data['lastposvisible'])
    list.append(data['ip'])
    list.append(data['belllist'])
    list.append(data['systemapplist'])
    list.append(data['screeninfo'])
    list.append(data['innerspace'])
    list.append(data['outerspace'])
    list.append(data['useragent'])
    list.append(data['label'])    
    return tuple(list)

def main_function(input_dfp):
    # get the new devicefp
    x = read_json(input_dfp)
        
    # to judge whether unique information is null;
        # both null: quit
        # both not null: judge whether match
        # one null: compute Pi
    user_id = x[0]    
    user_name = x[1]
    user_AndroidId = x[2]
    user_serialNumber = x[3]
    # user_serialNumber = "NULL"
    # print user_AndroidId,user_serialNumber
    
    # get user's benchmark’s unique info( maybe not unique)
    sql = "SELECT AndroidId,serialNumber FROM benchmark_android2 \
           WHERE uname = '%s'"%user_name
    unique_info = sql_fetchall(sql)
    # print "unique_info:",unique_info
    
    # both null: quit
    if (user_serialNumber == "NULL" and user_AndroidId == "NULL"):
        # print" Refused! please go to e-mail for verifying!"
        return False
    # both not null:
    elif(user_serialNumber != "NULL" and user_AndroidId != "NULL"):  
        # print "user_serialNumber is not NULL and user_AndroidId is not NULL"      
        # compare with benchmark,judge whether match
        #print user_AndroidId
        flag = 0
        for i in range(len(unique_info)):
            if (user_serialNumber != unique_info[i][1] or user_AndroidId != unique_info[i][0]):
                continue
            else:
                flag = 1
                # print "Unique info completely match! Approved！"
                # set label = 1
                sql = "UPDATE think_android SET label='1' where id = %d;" %user_id
                sql_zscg(sql)
                # update benchmark    
                update_benchmark(user_name,user_serialNumber,user_AndroidId,x)  
                return True                    
        if flag == 0:
            # print "1Unique info don't match! please go to e-mail for verifying!"
            return False
    # one null and the non-null matches: compute Pi
    elif(user_AndroidId != "NULL" and user_serialNumber == "NULL" ):
        # print "user_serialNumber is NULL!"
        flag = 0
        for i in range(len(unique_info)):
            if (user_AndroidId != unique_info[i][0]):   
                # print "flag is ",flag           
                continue                
            else:
                flag = 1
                print "flag is ",flag
                # select dfp's non-unique fields in database from table selected_android(include constructed abnormal data)
                sql = "select MAC,timeArea,autoLockTime,getLocationMethod,inputInfo,fontList, \
                    phoneBell,lastPosVisible,IP,bellList,systemAppList, screenInfo, innerSpace,\
                    outerSpace,userAgent,label from selected_android where uname = '%s'"%user_name+\
                    "and AndroidId = '%s'"%user_AndroidId
                inputData = sql_fetchall(sql)
                
                # select input_Device_fp ——> x's non-unique fields
                x_non_unique = x[4:]
                
                Pi = compute_reliability(inputData,x_non_unique)
                # print Pi
                threshold_value = 0.07
                if ( Pi > threshold_value ):
                    # set label = 1
                    sql = "UPDATE think_android SET label='1' where id = %d;" %user_id
                    sql_zscg(sql)
                    # if benchmark is integral, don't update benchmark; else update 
                    if (unique_info[i][0]!= "NULL" and unique_info[i][1]== "NULL"):
                        update_benchmark(user_name, user_serialNumber, user_AndroidId,x)
                    '''else:
                        # print "unique_info is not integral, don't update benchmark!" 
                    ''' 
                    return True
                else:
                    # set label = 0
                    sql = "UPDATE selected_android SET label='0' where id = %d;" %user_id
                    sql_zscg(sql)
                    return False
        if flag == 0:
            # print "2Unique info don't match! please go to e-mail for verifying!"  
            return False

    elif(user_serialNumber != "NULL" and user_AndroidId == "NULL"):
        # print "user_AndroidId is NULL!"
        flag = 0
        for i in range(len(unique_info)):
            if (user_serialNumber != unique_info[i][1]):
                continue
            else:
                flag = 1
                # select dfp's non-unique fields from table selected_android(include constructed abnormal data)
                sql = "select MAC,timeArea,autoLockTime,getLocationMethod,inputInfo,fontList, \
                    phoneBell,lastPosVisible,IP,bellList,systemAppList, screenInfo, innerSpace,\
                    outerSpace,userAgent,label from selected_android where uname = '%s'"%user_name+\
                "and serialNumber = '%s'"%user_serialNumber
                inputData = sql_fetchall(sql)
                
                # select input_Device_fp ——> x's non-unique fields
                x_non_unique = x[4:]
                
                Pi = compute_reliability(inputData,x_non_unique)
                threshold_value = 0.07
                if ( Pi > threshold_value ):
                    # set label = 1
                    sql = "UPDATE think_android SET label='1' where id = %d;" %user_id
                    sql_zscg(sql)
                    # if benchmark is integral, don't update benchmark; else update  
                    if (unique_info[i][0]== "NULL" and unique_info[i][1]!= "NULL"):
                        update_benchmark(user_name, user_serialNumber, user_AndroidId,x)
                    else:
                        print "unique_info is not integral, don't update benchmark!"  
                    return True                      
                else:
                    # set label = 0
                    sql = "UPDATE selected_android SET label='0' where id = %d;" %user_id
                    sql_zscg(sql)
                    return False
        if flag == 0:
            # print"3Unique info don't match! please go to e-mail for verifying!"
            return False        

app = Flask(__name__)

@app.route('/devices', methods=['POST'])
def device_auth():
    if not request.json or not 'id' in request.json:
        abort(400)
    request_data = request.get_json()
    
    device = request_data
    	
    result = main_function(request_data)
    if result==True:
      device['label'] = 1
    else:
    	device['label'] = 0
    
    #print device	
    return jsonify(device)

@app.route('/devices/lastest', methods=['GET'])
def get_device():
	  records = []
	  
	  sql = "SELECT * FROM benchmark_android2 ORDER BY id DESC LIMIT 5"
	  results = sql_fetchall(sql)
	  
	  for row in results:
	      result = {}
	      result['id'] = row[0]
	      result['uname'] = row[1]
	      result['androidid'] = row[2]
	      result['serialnumber'] = row[3]
	      result['mac'] = row[4]
	      result['timearea'] = row[5]
	      result['autolocktime'] = row[6]
	      result['getlocationmethod'] = row[7]
	      result['inputinfo'] = row[8]
	      result['fontlist'] = row[9]
	      result['phonebell'] = row[10]
	      result['lastposvisible'] = row[11]
	      result['ip'] = row[12]
	      result['belllist'] = row[13]
	      result['systemapplist'] = row[14]
	      result['screeninfo'] = row[15]
	      result['innerspace'] = row[16]
	      result['outerspace'] = row[17]
	      result['useragent'] = row[18]
	      result['label'] = row[19]
	      records.append(result)
	  
	  return jsonify(records)
if __name__ == '__main__':
    app.run(host='0.0.0.0')
      