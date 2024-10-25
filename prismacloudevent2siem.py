import logging
import logging.handlers
import requests
import json
import time
import urllib3
import pytz
urllib3.disable_warnings()
from datetime import datetime, timezone
from datetime import timedelta

### Set Variable ###
Path_to_console = "{{ Path_to_console }}" 
Prisma_API_access_ID = "{{ Prisma_API_access_ID }}"
Prisma_API_Secret_Key = "{{ Prisma_API_Secret_Key }}"

#### HÀM XỬ LÝ DỮ LIỆU
# Ham lay thoi gian hien tai theo gio UTC
def get_current_time():
  now = datetime.utcnow()
  iso_time = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
  return iso_time

# Get last delta Time
def get_incident_delta_time():
  now = datetime.utcnow()
  delta_time_incident = now - timedelta(hours=24) # Set last First time for Incident
  iso_time = delta_time_incident.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
  return iso_time

# change time Z to UTC+7
def change_time_z(now):
    return datetime.strptime(now, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc).astimezone(timezone(timedelta(hours=7))).strftime('%Y-%m-%d %H:%M:%S %Z')

# change timestamp to UTC+7
def change_time_stamp(time):
   utc_time = datetime.fromtimestamp(time / 1000, timezone.utc)
   tz = timezone(timedelta(hours=7))
   new_time = utc_time.astimezone(tz)
   return new_time.strftime('%Y-%m-%d %H:%M:%S %Z')

#### HÀM ĐẨY LOG
def push_log(x):
    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address = ('127.0.0.1',514))
    my_logger.addHandler(handler)
    my_logger.debug(x)

### HÀM LẤY TOKEN
def get_token(url):
    payload = {
        "username": Prisma_API_access_ID ,
        "password": Prisma_API_Secret_Key
    }
    headers = {'content-type': 'application/json'}
    response = requests.post(url, headers=headers, json=payload, verify = False)
    if response.ok:
        return response.json().get("token")
    else:
        print("Error occurred while retrieving the access token.")
        return None

    
### HÀM LẤY LOG
def get_management_audit_logs(timeamount, timeunit):
    url = "https://api.sg.prismacloud.io/audit/redlock?timeType=relative&timeAmount=" + timeamount + "&timeUnit=" + timeunit
    token_url = "https://api.sg.prismacloud.io/login"
    headers = {
      'accept': 'application/json; charset=UTF-8',
      'content-type': 'application/json',
      'Authorization': 'Bearer ' + str(get_token(token_url))
    }
    response = requests.get(url, headers=headers, verify = False).json()
    for audit in response:
        user = audit.get("user")
        if user == user_API:
            pass
        else:
            audit["timestamp"] = change_time_stamp(audit["timestamp"])
            push_log(audit)
            print(audit)
    print("Get Audit Running...")

def get_incident_audit_events(from_time):
    global last_incident_time
    current_time = get_current_time()
    url = Path_to_console +"/api/v30.00/audits/incidents?sort=time&from=" + from_time + "&to=" + current_time
    token_url = Path_to_console + "/api/v22.12/authenticate"
    headers = {
      'accept': 'application/json; charset=UTF-8',
      'content-type': 'application/json',
      'Authorization': 'Bearer ' + str(get_token(token_url))
    }
    response = requests.get(url, headers=headers, verify = False).json()
    last_incident_time = response[-1]["time"]
    print("Get incident Running...")
    for incident in response[1:] if from_time != get_incident_delta_time() else response:
        time = incident["time"]
        incident["time"] = change_time_z(time)
        push_log(incident)
        print(incident)
    print("Sleep from: " + change_time_z(current_time))

### HÀM XỬ LÝ
user_API = "dat.mai @svtech.com.vn" # Ten user dung de goi API(Exept user nay de khong lay log goi API)
firsttime = True
last_delta_time = get_incident_delta_time()
def process():
    global time_to_get
    global firsttime
    global last_incident_time
    global last_delta_time
    starttime = time.time()
    if(firsttime==True):
        get_management_audit_logs("12","hour") # Set First time for audit minute, day, hour, week, month, year
        get_incident_audit_events(last_delta_time)
        firsttime = False
    else:
        get_management_audit_logs(time_to_get,"minute") # minute, day, hour, week, month, year
        get_incident_audit_events(last_incident_time)

    endtime = time.time()
    elapsed_time = endtime - starttime
    time_to_get = str(int(elapsed_time // 60 + 1))
    time.sleep(60.0 - elapsed_time % 60.0) # Cho cho den phut tiep theo chay lai

while True:
    process()
