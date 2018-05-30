'''
library for ezo
(c) 2018 - Robin A. Gist - All Rights Reserved
'''


from solc import compile_source
from web3 import Web3, WebsocketProvider, HTTPProvider
from core.helpers import get_url, get_hash, get_account
import pymongo
from datetime import datetime
import asyncio
from multiprocessing import Process


async def event_loop(event_filter, interval=1):
    while True:
        for event in event_filter.get_new_entries():
            print("got an event: {}".format(event))
            handle_event(event)
        print("in event loop")
        await asyncio.sleep(interval)


def handle_event(event):
    print("event: {}".format(event))


class EZO:
    '''
    Easy Oracle (ezo) base class

    '''

    _listeners = dict()

    def __init__(self, config, w3=False):
        self.config = config
        if w3:
            self.dial()
        self.connect()


    def dial(self, url=None):
        '''
        connects to a node

        :param url: string (optional) - resource in which to connect.
        if not provided, will use default for the stage
        :returns: provider, error
        '''
        if not url:
            url = get_url(self.config, self.target)

        try:
            if url.startswith('ws'):
                self.w3 = Web3(WebsocketProvider(url))
            elif url.startswith('http'):
                self.w3 = Web3(HTTPProvider(url))

        except Exception as e:
            return None, e

        return self.w3, None

    def connect(self, url=None):
        '''
        connects to MongoDB instance

        :param url: (string) full URL for the mongo instance
        :return: database handle, error
        '''

        if not url:
            url = self.config["database"]["url"]
        name = self.config["database"]["name"]

        try:
            self.client = pymongo.MongoClient(url)
            self.db = self.client[name]
        except Exception as e:
            return None, e
        return self.db, None


    def view_deployments(self):
        deploys = list()
        try:
            for deploy in self.db.deployments.find({}).sort('timestamp', pymongo.DESCENDING):
                deploys.append(deploy)
        except Exception as e:
            return None, e
        return deploys, None

    def view_contracts(self):
        contracts = list()
        try:
            for contract in self.db.contracts.find({}).sort('timestamp', pymongo.DESCENDING):
                contracts.append(contract)
        except Exception as e:
            return None, e
        return contracts, None

    def view_source(self, hash):
        pass


    def close(self):
        '''
        close mongo and web3 connections
        :return: None
        '''
        self.client.close()


    def start(self, contract_hashes):
        '''
        loads the contracts from their hashes and starts their event listeners
        :param contracts:
        :return:
        '''

        print("ezo start - hashes: {}".format(contract_hashes))
        if isinstance(contract_hashes, str):
            contract_hashes = [contract_hashes]

        if not isinstance(contract_hashes, list):
            return None, "error: expecting a string, or a list of contract hashes"

        jobs = []
        for hash in contract_hashes:
            print("hash: {}".format(hash))
            c, err = Contract.create_from_hash(hash, self)
            if err:
                return None, err

            address = Contract.get_address(hash, self)
            if not address:
                return None, "error: no deployment address for {} on target stage {}".format(hash, self.target)

            p = Process(target=c.listen, args=(address,))
            p.daemon = True
            jobs.append(p)
            p.start()

        for pr in jobs:
            pr.join()


class Contract:


    def __init__(self, name, ezo):
        self.name = name
        self._ezo = ezo
        self.timestamp = datetime.utcnow()


    def deploy(self):
        '''
        deploy this contract
        :param w3: network targeted for deployment
        :param account:  the account address to use
        :return: address, err
        '''

        account = get_account(self._ezo.config, self._ezo.target)
        try:
            deployments = self._ezo.db["deployments"]
        except Exception as e:
            return None, e

        try:
            ct = self._ezo.w3.eth.contract(abi=self.abi, bytecode=self.bin)
            #TODO - proper gas calculation

            tx_hash = ct.deploy(transaction={'from': account, 'gas': 405000})
            tx_receipt = self._ezo.w3.eth.waitForTransactionReceipt(tx_hash)
            address = tx_receipt['contractAddress']

        except Exception as e:
            return None, e

        d = dict()
        d["contract-name"] = self.name
        d["hash"] = self.hash
        d["tx-hash"] = tx_hash
        d["address"] = address
        d["target"] = self._ezo.target
        d["timestamp"] = datetime.utcnow()

        # save the deployment information
        try:
            iid = deployments.insert(d)

        except Exception as e:
            return None, e
        return address, None


    def listen(self, address):
        '''
        starts event listener for the contract
        :return:
        '''
        address = "0x8cdaf0cd259887258bc13a92c0a6da92698644c0"
        print("listening to address: {}".format(address))

        event_filter = self._ezo.w3.eth.filter({"address": address, "toBlock": "latest"})
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(asyncio.gather(event_loop(event_filter)))
        except Exception as e:
            return None, e

        finally:
            loop.close()


    # saves the compiled contract essentials to mongo
    def save(self):
        try:
            contract_collection = self._ezo.db["contracts"]
        except Exception as e:
            return None, e

        c = dict()
        c["name"] = self.name
        c["abi"] = self.abi
        c["bin"] = self.bin
        c["source"] = self.source
        c["hash"] = get_hash(self.source)
        c["timestamp"] = self.timestamp

        try:
            iid = contract_collection.insert(c)
        except Exception as e:
            return None, e
        return iid, None

    # get the


    @staticmethod
    def create_from_hash(hash, ezo):
        '''
        given the hash of a contract, returns a contract  from the data store
        :param hash: (string) hash of the contract source code
        :param ezo: ezo instance
        :return: contract instance, error
        '''
        try:
            cp = ezo.db.contracts.find_one({"hash": hash})
        except Exception as e:
            return None, e

        # create a new Contract
        c = Contract(cp["name"], ezo)
        c.abi = cp["abi"]
        c.bin = cp["bin"]
        c.hash = cp["hash"]
        c.source = cp["source"]
        c.timestamp = cp["timestamp"]

        return c, None



    @staticmethod
    def load(filepath):
        '''
        loads a contract file

        :param filepath: (string) - contract filename
        :return: source, err
        '''

        try:
            with open(filepath, "r") as fh:
                source = fh.read()
        except Exception as e:
            return None, e
        return source, None


    @staticmethod
    def compile(source, ezo):
        '''
        compiles the source code

        :param source: (string) - contract source code
        :param ezo: - ezo reference for Contract object creation
        :return: (list) compiled source
        '''
        try:
            compiled = compile_source(source)
            compiled_list = []
            for name in compiled:
                c = Contract(name, ezo)
                interface = compiled[name]
                c.abi = interface['abi']
                c.bin = interface['bin']
                compiled_list.append(c)

        except Exception as e:
            return None, e
        return compiled_list, None

    @staticmethod
    def get_address(hash, ezo):
        '''
        fetches the contract address of deployment

        :param hash: the contract file hash
        :return: (string) address of the contract
        '''
        target = ezo.target
        try:
            address = ezo.db.deployments.find_one({"hash": hash, "target": target})
        except Exception as e:
            return None, e
        return address["address"] if "address" in address else None


class DB:
    '''
    data storage abstraction layer
    serializes/unserializes contract and deployment data

    '''

    _cache = dict()
    _db = None

    def __init__(self):
        if not DB._db:
            
        pass

    def save(self, storage_type, key, value):
        if not isinstance(storage_type, str):
            return None, "storage_type must be a string"
        if not isinstance(key, str):
            return None, "key must be a string"

        pkey = DB.pkey(storage_type, key)


        # pickle value
        b_val = pickle.dumps(value)

        # store in leveldb



    def replace(self, storage_type, key, value):
        pass


    def load(self, storage_type, key):
        pass

    def delete(self, storage_type, key):
        pass

    @staticmethod
    def pkey(storage_type, key):
        return "{}__{}".format(storage_type, key)

