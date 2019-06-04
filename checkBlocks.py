#sudo apt-get update
#sudo apt-get -y install python3-pip

#Require installation
from nano import RPCClient #pip3 install nano-python
import schedule #pip3 install schedule
import asyncio #pip3 install asyncio
import websockets #pip3 install websockets

#Standard python
import json
import datetime
import time
import requests

#Settings
rpc = RPCClient('http://127.0.0.1:55000') #nano node address and port(I use this in node config: "::ffff:127.0.0.1"). You can also try with "http://[::1]:55000"
websocketURL = '[::1]:57000' #websocket url defined in nano config.json (must be enabled in config if you want confirmation per second)
tpsInterval = [10, 60, 300, 600, 3600] #intervals defined in seconds for local logging (any set of numbers work)
enableStatfiles = False #set to True (not true) to enable saving to log files
enableOutput = True #set to True (not true) to enable console logs
enableCPS = False #set to True to enable confirmations per second from websocket subscription
statsPath = 'stats' #path to statfile basename (extension will be added automatically and two files for each interval will be created)

#If sending to server to collect stats
enableServer = False #set to True (not true)
secret = 'password' #secret ID for server to accept data
name = 'Awesome node' #custom node name will be visible on stat webpage

serverInterval = 15 #interval in seconds to push stat to server (server is coded to only accept a certain value here, only change if running own server)
serverURI = 'https://beta.nanoticker.info/tps_beta_push.php' #php code to accept request. Don't change unless you have own server

#Vars (dont touch)
headers = { "charset" : "utf-8", "Content-Type": "application/json" }
countOld = []
confCount = [] #contains confirmation count for different intervals
cps = [] #contains CPS for different intervals
for i in tpsInterval:
  countOld.append(0)
  confCount.append(0) #for CPS subscription
  cps.append(0)

#Sheduled job for TPS
def jobRPC(interval):
  #Get latest block count from nano RPC service
  if not rpc:
    return

  arred = lambda x,n : x*(10**n)//1/(10**n) #decimal point function | arred(3.1415,2) => 2 decimals

  try:
    blockCount = rpc.block_count()
    blkCount = blockCount['count']
    blkUnch = blockCount['unchecked']
    peers = rpc.peers()
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    #Calculate TPS based on previous values
    global countOld
    if countOld[interval] == 0: #first iteration => tps=0
      for i,int in enumerate(countOld): #initialize memory
        countOld[i] = blkCount
      tps = 0
    else:
      tps = (blkCount - countOld[interval]) / tpsInterval[interval] #tps based on previous iteration
    countOld[interval] = blkCount #update value for next iteration

    #Create json and csv definitions
    entryJSON = {'time':timestamp, 'count':blkCount, 'unchecked':blkUnch, 'peers': len(peers), 'interval': tpsInterval[interval], 'tps':arred(tps,2), 'cps':arred(cps[interval],2)}
    entryCSV = [timestamp, str(blkCount), str(blkUnch), str(len(peers)), str(tpsInterval[interval]), str(arred(tps,2)), str(arred(cps[interval],2))]

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
  #Get latest block count from nano RPC service
  if not rpc:
    return

  try:
    blockCount = rpc.block_count()
    blkCount = blockCount['count']
    blkUnch = blockCount['unchecked']
    peers = rpc.peers()
    version = rpc.version()['node_vendor']
    unixtime = time.time()

    postJSON = {'time':unixtime, 'count':blkCount, 'unchecked':blkUnch, 'interval': serverInterval, 'id': secret, 'name': name, 'peers': len(peers), 'version':version}

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
for i,int in enumerate(tpsInterval):
  schedule.every(int).seconds.do(jobRPC, interval=i)

#Schedule job for sending stat to server
if enableServer:
  schedule.every(serverInterval).seconds.do(jobRPCServer)
  jobRPCServer() #Init values one time directly

#Subscription service via websockets
def subscription(topic: str, ack: bool=False, options: dict=None):
    d = {"action": "subscribe", "topic": topic, "ack": ack}
    if options is not None:
        d["options"] = options
    return d

async def cpsTask():
    try:
      async with websockets.connect(f"ws://{websocketURL}") as websocket:
        # Subscribe to confirmations
        # You can also add options here following instructions in
        #   https://github.com/nanocurrency/nano-node/wiki/WebSockets

        await websocket.send(json.dumps(subscription("confirmation", ack=True)))
        #print(await websocket.recv())  # ack

        init = True
        startTimes = []
        global confCount
        global cps

        while 1:
          rec = json.loads(await websocket.recv())
          topic = rec.get("topic", None)
          if topic:
            message = rec["message"]

            if topic == "confirmation":
              #print("Block confirmed: {}".format(message))
              #Start the clock on first confirmation
                if init:
                  init = False

                  for i in tpsInterval:
                    startTimes.append(time.time()) #start measure time for different intervals

                for i,conf in enumerate(confCount):
                  confCount[i] = confCount[i] + 1

                  #Update CPS 1 second before the TPS function prints it or it will not be updated until next iteration
                  if ((time.time() - startTimes[i]) >= tpsInterval[i] - 1):
                    cps[i] = conf / (time.time() - startTimes[i])
                    confCount[i] = 0
                    startTimes[i] = time.time() #sreset time

    except ConnectionRefusedError:
      print("Error connecting to websocket server. Make sure you have enabled it in ~/Nano/config.json")

async def tpsTask():
  jobRPC(interval=0)
  while 1:
    schedule.run_pending()
    await asyncio.sleep(1)

loop = asyncio.get_event_loop()
if enableCPS:
  loop.create_task(cpsTask())
loop.create_task(tpsTask())
loop.run_forever()
