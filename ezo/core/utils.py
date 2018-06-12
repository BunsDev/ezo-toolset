import json
from eth_account import Account
from xkcdpass import xkcd_password as xp
from core.helpers import red, cyan, yellow


def create_ethereum_account():
    ac = Account.create()
    wf = xp.locate_wordfile()
    words= xp.generate_wordlist(wordfile=wf, min_length=5, max_length=8)

    password_str = xp.generate_xkcdpassword(words)
    print(cyan("password string to decrypt private key -- please store in safe location:"))
    print()
    print(yellow(password_str))
    print()
    print(cyan("address:"))
    print(yellow(ac.address))

    ks = json.dumps(Account.encrypt(ac.privateKey, password_str), indent=2)
    print(red(ks))


def gen_event_handler_code(event_name):

    template = '''


# This code automatically generated by ezo.  Only modify where suggested.
#
# data is an instance of ContractEvent
# contract is the calling instance of Contract - it is used to send a response

from core.helpers import red, cyan, yellow, magenta, blue
from core.lib import EZO
from datetime import datetime

'''

    template += "event_name = '{}'".format(event_name)
    template += '''


def handler(data, contract):

    

    ### put your code here
    ts = datetime.now()
    EZO.log.info(("event: {:25s} contract: {:35s} address {:40s} timestamp: {:25s}").
                 format(yellow(event_name), magenta(contract.name.replace("<stdin>:", "")), blue(data.address), magenta(ts)))
    ### put your code here
    
    ### uncomment the code below to build a response object
    # response = dict()
    # response["address"] = data.address  # <<< the contract's address from the data 
    # response["function"] = None         # <<< replace None with the Contract function that will be called
    # response["params'] = None           # <<< replace None with a list of your function's data parameters
     
    ### uncomment the code below to send a response to the contract function
    # _, err = contract.response(response)
    # if err:
    #     return None, err
   
    return None, None
    '''

    return template


def create_blank_config_obj():

    template = '''
{
	"ezo": {
		"target": {
			"test": {
				"account": "0x627306090abaB3A6e1400e9345bC60c78a8BEf57",
				"url": "http://127.0.0.1:7545",
				"network": "ganache"
			},
			"test2": {
				"account": "",
				"url": "http://localhost:8545",
				"network": "ganache-cli"
			}
		},
		"contract-dir": "",
		"handlers-dir": "",
		"leveldb": "/tmp/ezodb",
		"poll-interval": 1,
		"project-name": ""
	}
}
'''

    return json.loads(template)


def create_sample_contracts_1():
    # WeatherOracle

    template = '''
pragma solidity ^0.4.21;

// Temperature Oracle 
// generated by ezo
// use at your own risk
//
contract TemperatureOracle {

    address public owner;
    uint public temp;
    uint public timestamp;

    event TempRequest(address sender);
    event FilledRequest(uint rtemp);

    function constructor() public {
        temp = 0;
        owner = msg.sender;
    }

    function request() public returns (string) {
        emit TempRequest(msg.sender);
        return "sent";
    }

    function fill(uint rtemp) public returns (uint){
        temp = rtemp;
        emit FilledRequest(rtemp);
        return temp;
    }


}   
    '''
    return template


def create_sample_contracts_2():

    #TimestampOracle

    template = '''
    
pragma solidity ^0.4.21;

// Timestamp Oracle
// Generated by ezo
//
// use at your own risk
//

contract TimestampRequestOracle {

    address public owner;
    uint public _timestamp;

    event TimeRequest(address sender);
    event RequestFilled(address sender,uint timestamp);


    function constructor() public {
        _timestamp = 0;
        owner = msg.sender;
    }

    function sendTimestampRequest() public {
        emit TimeRequest(msg.sender);
    }

    function setTimestamp(uint timestamp) public {
        _timestamp = timestamp;
        emit RequestFilled(msg.sender, _timestamp);
    }

    function getTimestamp() public returns (uint) {
        return _timestamp;
    }

}
    
    '''

    return template