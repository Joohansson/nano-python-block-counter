#sudo apt-get update
#sudo apt-get -y install python3-pip
#Require installation
from nano import RPCClient #pip3 install nano-python
import schedule #pip3 install schedule

#Standard python
import json
import datetime
import time
import requests

#Settings
rpc = RPCClient('http://127.0.0.1:55000') #nano node address and port(I use this in node config: "::ffff:127.0.0.1"). You can also try with "http://[::1]:55000"
tpsInterval = [60,300,1800] #intervals defined in seconds for local logging (any set of numbers work)
enableStatfiles = False #set to True (not true) to enable saving to log files
enableOutput = True #set to True (not true) to enable console logs
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
for i in tpsInterval:
  countOld.append(0)

#Sheduled job for TPS
def jobRPC(interval):
  #Get latest block count from nano RPC service
  if not rpc:
    return

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
    entryJSON = {'time':timestamp, 'count':blkCount, 'unchecked':blkUnch, 'peers': len(peers), 'interval': tpsInterval[interval], 'tps':tps}
    entryCSV = [timestamp, str(blkCount), str(blkUnch), str(len(peers)), str(tpsInterval[interval]), str(tps)]

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

#Run one time now
jobRPC(interval=0)

while 1:
  schedule.run_pending()
  time.sleep(1)
