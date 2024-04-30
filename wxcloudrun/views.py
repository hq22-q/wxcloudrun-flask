import json
import re
from flask import Flask, request, jsonify
import requests
from flask_redis import FlaskRedis
from run import app
from wxcloudrun.response import make_succ_response, make_err_response

# flask-redis 的配置和初始化
app.config['REDIS_URL'] = 'redis://:h9qAztRcB8berfT03Qmr02sKHwDOXPyU@3.0.17.160:16666/0'
redis_client = FlaskRedis(app)


@app.route('/attendance', methods=['POST'])
def get_attendance():  # put application's code here
    # 可以通过 request 的 args 属性来获取参数
    where = ''
    parma = request.get_json()
    id = parma["id"]
    # # 写入 redis 中
    # # 通过管道 pipeline 来操作 redis，以减少客户端与 redis-server 的交互次数。
    # list = ["123", "456"]
    # json_array = json.dumps(list)
    # redis_client.set("attendanceID",json_array)

    # 从 Redis 中获取 JSON 字符串
    json_array_from_redis = redis_client.get('attendanceID')

    # 解析 JSON 字符串为数组
    id_list = json.loads(json_array_from_redis)
    print(id_list)
    if id not in id_list:
        return make_err_response("此工号不可查询!")

    dateCode = parma["dateCode"]
    if (dateCode == '1'):
        # 本月
        where = 'Month(A.Date) = month(getdate()) and Year(A.Date) =year(getdate())'
    elif (dateCode == '2'):
        # 上月
        where = 'Month(A.Date) = month(dateadd(m,-1,getdate())) and Year(A.Date) =year(dateadd(m,-1,getdate()))'
    elif (dateCode == '3'):
        # 本年
        where = 'Year(A.Date) =year(getdate())'
    elif (dateCode == '4'):
        # 上年
        where = 'Year(A.Date) =year(dateAdd(year,-1,getdate()))'
    elif (dateCode == '5'):
        # 具体范围
        beginDate = parma["beginDate"]
        endDate = parma["endDate"]
        where = "CONVERT(DATETIME,A.Date) >= CONVERT(DATETIME,'" + beginDate + "') and CONVERT(DATETIME,A.Date) <= CONVERT(DATETIME,'" + endDate + "')"
    # 请求
    # c0-id=7166_1712905079013
    data = ("""callCount=1
c0-scriptName=ajax_DatabaseAccessor
c0-methodName=executeQuery

c0-param0=string:HRM117
c0-param1=string:select distinct code,CnName,Department,CardCode,Date,Time,ScName from ( SELECT distinct B.code,B.CnName,C.Name as Department,A.CardCode,Convert(nvarchar,A.Date,23) Date,min(time) MinTime,max(time) MaxTime,CodeInfo.ScName  FROM AttendanceCollect as A  LEFT JOIN Employee as B on A.EmployeeId=B.EmployeeId  LEFT JOIN Department as C ON C.DepartmentId=B.DepartmentId  LEFT JOIN Machine AS D ON A.MachineId=D.MachineId  LEFT JOIN AttendanceCollectLog AS F ON A.AttendanceCollectLogId=F.AttendanceCollectLogId  LEFT JOIN Employee AS E ON F.CollectEmployeeId=E.EmployeeId  LEFT JOIN CodeInfo ON CodeInfo.CodeInfoId = A.RepairId  where B.code = '""" +

            id + "' and " + where + """ group by B.code,B.CnName,C.Name,A.CardCode,ScName,Convert(nvarchar,A.Date,23)  ) MM  UNPIVOT(Time for Subject in(MinTime,MaxTime) )as up order by Date,Time 
c0-param2=null:null
c0-param3=null:null
xml=true""")

    url = "http://efgpcn.digiwin.com/NaNaWeb/dwrDefault/exec/ajax_DatabaseAccessor.executeQuery.dwr"
    headers = {'Accept': '*/*',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
               'Cache-Control': 'no-cache',
               # 'Content-Length': '1395',
               'Content-Type': 'text/plain; charset=utf-8',
               'Host': 'efgpcn.digiwin.com',
               'Origin': 'http://efgpcn.digiwin.com',
               'Pragma': 'no-cache',
               'Proxy-Connection': 'keep-alive',
               'Referer': 'http://efgpcn.digiwin.com/NaNaWeb/GP/WMS/PerformWorkItem/CallFormHandler?hdnMethod=handleForm',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
               }

    response = requests.post(url=url, data=data, headers=headers)

    text = response.text
    # 定义正则表达式
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    time_pattern = r'\"(\d{1,2}:\d{2}(?::\d{2})?)\"'

    # 使用正则表达式提取日期
    dates = re.findall(date_pattern, text)
    times = re.findall(time_pattern, text)

    # 打印提取的日期
    print("日期", dates)
    print("时间", times)
    data = []
    for date, time in zip(dates, times):
        item = {}
        item["date"] = date
        item["time"] = time
        data.append(item)

    return make_succ_response(data)
