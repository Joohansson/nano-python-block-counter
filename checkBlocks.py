#sudo apt-get update
#sudo apt-get -y install python3-pip

#Require installation
from nano import RPCClient #pip3 install nano-python
import schedule #pip3 install schedule
import asyncio #pip3 install asyncio

#Standard python
import json
import datetime
import time
import requests
import os

#Settings
rpc = RPCClient('http://[::1]:55000') #nano node address and port(I use this in node config: "::ffff:127.0.0.1"). You can also try with "http://[::1]:55000"
tpsInterval = [30, 300, 600, 3600] #intervals defined in seconds for local logging (any set of numbers work)
enableStatfiles = False #set to True (not true) to enable saving to log files
enableOutput = True #set to True (not true) to enable console logs
includeCemented = True #if include cemented block count from node RPC command (v19+)
statsPath = 'stats' #path to statfile basename (extension will be added automatically and two files for each interval will be created)

#If sending to server to collect stats
enableServer = False #set to True (not true)
secret = 'secret password not given by default' #secret ID for server to accept data
name = 'Awesome Node' #custom node name will be visible on stat webpage

serverInterval = 15 #interval in seconds to push stat to server (server is coded to only accept a certain value here, only change if running own server)
serverCPSInterval = 300 #interval in seconds for calculating CPS, please don't change
serverURI = 'https://beta.nanoticker.info/tps_beta_push.php' #php code to accept request. Don't change unless you have own server

#Vars (dont touch)
headers = { "charset" : "utf-8", "Content-Type": "application/json" }
countOld = []
countOldCPS = []
serverCPSRolling = []
countOldCPSServer = 0

for i in tpsInterval:
  countOld.append(0)
  countOldCPS.append(0)

#Sheduled job for TPS
def jobRPC(interval):
  global countOld
  global countOldCPS

  #Get latest block count from nano RPC service
  if not rpc:
    return

  arred = lambda x,n : x*(10**n)//1/(10**n) #decimal point function | arred(3.1415,2) => 2 decimals

  try:
    #get cemented block count
    if (includeCemented):
      params = {
          "action": "block_count",
          "include_cemented": "true"
      }
      resp = requests.post(url=nodeUrl, json=params)
      blockCount = resp.json()
      blkCount = int(blockCount['count'])
      blkUnch = int(blockCount['unchecked'])
      cemented = int(blockCount['cemented'])

      #Calculate CPS based on previous values
      if countOldCPS[interval] == 0: #first iteration => cps=0
        for i,into in enumerate(countOldCPS): #initialize memory
          countOldCPS[i] = cemented
        cps = 0
      else:
        cps = (cemented - countOldCPS[interval]) / tpsInterval[interval] #tps based on previous iteration
      countOldCPS[interval] = cemented #update value for next iteration

    else:
      blockCount = rpc.block_count()
      blkCount = blockCount['count']
      blkUnch = blockCount['unchecked']
      cemented = 0
      cps = 0

    peers = rpc.peers()
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    #Calculate TPS based on previous values
    if countOld[interval] == 0: #first iteration => tps=0
      for i,into in enumerate(countOld): #initialize memory
        countOld[i] = blkCount
      tps = 0
    else:
      tps = (blkCount - countOld[interval]) / tpsInterval[interval] #tps based on previous iteration
    countOld[interval] = blkCount #update value for next iteration

    #Create json and csv definitions
    entryJSON = {'time':timestamp, 'count':blkCount, 'unchecked':blkUnch, 'cemented':cemented, 'peers': len(peers), 'interval': tpsInterval[interval], 'bps':arred(tps,2), 'cps':arred(cps,2)}
    entryCSV = [timestamp, str(blkCount), str(blkUnch), str(cemented), str(len(peers)), str(tpsInterval[interval]), str(arred(tps,2)), str(arred(cps,2))]

    if enableOutput:
      print(json.dumps(entryJSON))

  except Exception as e:
    print('Could not get blocks from node. Error: %r' %e)
    return

  if enableStatfiles:
    #Append stats to file or create new file
    try:
      with open(statsPath + '_' + str(tpsInterval[interval]) + '.json', 'a') as outfile:
        outfile.write('%r\n' %entryJSON)

    except Exception as e:
      print('Could not save json file. Error: %r' %e)
      return

    #Append stats to file or create new file
    try:
      with open(statsPath + '_' + str(tpsInterval[interval]) + '.txt', 'a') as outfile:
        #Convert all of the items in lst to strings (for str.join)
        lst = map(str, entryCSV)
        #Join the items together with commas
        line = ";".join(lst)
        outfile.write(line+"\n")

    except Exception as e:
      print('Could not save csv file Error: %r' %e)
      return

#Job for pushing to server
def jobRPCServer():
  global serverCPSRolling
  global countOldCPSServer

  #Get latest block count from nano RPC service
  if not rpc:
    return

  try:
    #get cemented block count
    if (includeCemented):
      params = {
          "action": "block_count",
          "include_cemented": "true"
      }
      resp = requests.post(url=nodeUrl, json=params)
      blockCount = resp.json()
      blkCount = int(blockCount['count'])
      blkUnch = int(blockCount['unchecked'])
      cemented = int(blockCount['cemented'])

      #Calculate CPS based on previous values
      if countOldCPSServer == 0: #first iteration => cps=0
        serverCPS = 0
      else:
        serverCPS = (cemented - countOldCPSServer) / serverInterval #tps based on previous iteration
      countOldCPSServer = cemented #update value for next iteration

      serverCPSRolling.append(cemented)
      if (len(serverCPSRolling) > (serverCPSInterval / serverInterval + 1)):
        serverCPSRolling.pop(0)
      if (len(serverCPSRolling) - 1 > 0):
        serverCPS = (serverCPSRolling[-1] - serverCPSRolling[0]) / ((len(serverCPSRolling) - 1) * serverInterval)
      else:
        serverCPS = 0

    else:
      blockCount = rpc.block_count()
      blkCount = blockCount['count']
      blkUnch = blockCount['unchecked']
      cemented = 0
      serverCPS = 0

    peers = rpc.peers()
    version = rpc.version()['node_vendor']
    unixtime = time.time()

    postJSON = {'time':unixtime, 'count':blkCount, 'unchecked':blkUnch, 'interval': serverInterval, 'id': secret, 'name': name, 'peers': len(peers), 'version': version, 'cps': serverCPS}

  except Exception as e:
    print('Could not get blocks from node. Error: %r' %e)
    return

  #Send data to remote server
  try:
    r = requests.post(serverURI, json=postJSON)
    #print(r.json())
    if r.json() == 401:
      print('Wrong password for server')
    elif not r.status_code == 200:
      print('Could not connect to remote server. Http code: %r' %r.status_code)

  except Exception as e:
    print('Could not post result to remote server. Error: %r' %e)
    return

#Define scheduled job
for i,into in enumerate(tpsInterval):
  schedule.every(into).seconds.do(jobRPC, interval=i)

#Schedule job for sending stat to server
if enableServer:
  schedule.every(serverInterval).seconds.do(jobRPCServer)
  jobRPCServer() #Init values one time directly

async def tpsTask():
  jobRPC(interval=0) #init
  while 1:
    schedule.run_pending()
    await asyncio.sleep(0.01)

loop = asyncio.get_event_loop()
loop.create_task(tpsTask())
loop.run_forever()
