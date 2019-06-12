# nano-python-block-counter
Simple python script to count blocks and unchecked blocks from a nano currency node using RPC.

Library used: [nano-python](https://github.com/dourvaris/nano-python)


Outputs nano block count from node in format (Time in UTC, TPS=Transactions per second, CPS=Confirmations per second):

* JSON: {"time": "2018-08-20 19:29:49", "count": 1931263, "unchecked": 8115, "peers: 10", "interval": 10, "tps": 1.61, "cps": 1.61}
* CSV: Time; Count; Unchecked; Peers; Interval; TPS; CPS

Save stats to json and csv files

### Instructions
* Install python version > 3 and pip (sudo apt-get -y install python3-pip)
* pip3 install nano-python
* pip3 install schedule
* pip3 install asyncio
* pip3 install websockets
* Change settings in checkBlocks.py to match your nano node path, intervals and file path. Logfile and console output are optional. enableCPS is only available for node v19 and above (don't forget to enable websocket in the nano config).
* Run with python3 checkBlocks.py

### Optional: Push stat to [Demo server](https://beta.nanoticker.info)
* Change settings to match server settings. You can get "secret" from me on [Reddit](https://www.reddit.com/user/joohansson/) if you have a good node and want to test nano beta.
* Set enableServer = True

**Demo Server also supports [Nano Node Monitor](https://github.com/NanoTools/nanoNodeMonitor)**
