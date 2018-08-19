#Outputs nano block count from node in format:
#JSON: {'time': '2018-08-18 15:52:05', 'count': 1723175, 'unchecked': 8685}
#CSV: 2018-08-18 15:52:05;1723175;8685
#Save stats to json and csv files

#Instructions:
#Install python > 3 and pip3
#pip3 install nano-python
#pip3 install schedule
#Change settings below and run with python3 blocks.py


#Require installation
from nano import RPCClient
import schedule

#Standard python
import json
import datetime
import time

#Settings
rpc = RPCClient('http://127.0.0.1:55000') #nano node address and port
tps_interval = 5 #update interval in seconds
statsPathJson = 'stats.json' #path to statfile json
statsPathCSV = 'stats.txt' #path to statfile csv

#Sheduled job for TPS
countOld = 0
def jobRPC():
  #Get latest block count from nano RPC service
  if not rpc:
    return

  try:
    blockCount = rpc.block_count()
    blkCount = blockCount['count']
    blkUnch = blockCount['unchecked']
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    global countOld
    if countOld == 0: #first iteration => tps=0
      countOld = blkCount
    tps = (blkCount - countOld) / tpsInterval #tps based on previous iteration
    countOld = blkCount #update value for next iteration

    entryJSON = {'time':timestamp, 'count':blkCount, 'unchecked':blkUnch, 'TPS':tps}
    entryCSV = [timestamp,str(blkCount),str(blkUnch),str(tps)]
    print(entryJSON)

  except Exception as e:
    print('Could not get blocks from node. Error: %r' %e)
    return

  #Append stats to file or create new file
  try:
    with open(statsPathJson, 'a') as outfile:
      outfile.write('%r\n' %entryJSON)

  except Exception as e:
    print('Could not save json file. Error: %r' %e)
    return

  #Append stats to file or create new file
  try:
    with open(statsPathCSV, 'a') as outfile:
      #Convert all of the items in lst to strings (for str.join)
      lst = map(str, entryCSV)
      #Join the items together with commas
      line = ";".join(lst)
      outfile.write(line+"\n")

  except Exception as e:
    print('Could not save csv file Error: %r' %e)
    return

#Define scheduled job for coinmarketcap, 20 sec
schedule.every(tpsInterval).seconds.do(jobRPC)

while 1:
  schedule.run_pending()
  time.sleep(1)
