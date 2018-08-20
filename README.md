# nano-python-block-counter
Simple python script to count blocks and unchecked blocks from a nano currency node using RPC.

Library used: [nano-python](https://github.com/dourvaris/nano-python)


Outputs nano block count from node in format (Time in UTC):

* JSON: {'time': '2018-08-18 15:52:05', 'count': 1723175, 'unchecked': 8685}
* CSV: 2018-08-18 15:52:05;1723175;8685

Save stats to json and csv files

### Instructions
* Install python version > 3 and pip (sudo apt-get -y install python3-pip)
* pip3 install nano-python
* pip3 install schedule
* Change settings in checkBlocks.py to match your nano node, interval and file paths
* Run with python3 checkBlocks.py

### Optional: Push stat to [Demo server](https://nanoticker.info/tps_beta.php)
* Change settings to match server settings. You can get "secret" from me on [Reddit](https://www.reddit.com/user/joohansson/) if you have a good node and want to test nano beta.
