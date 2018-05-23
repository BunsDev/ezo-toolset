import json, xxhash


# sets up the current directory for an ezoracle project
def initialize():
    # copy the config.json template to the current directory
    # load the config.json template
    # create the default directories
    pass


# load configuration file
def load_configuration(configfile):
    print("CONFIG {}".format(configfile))
    try:
        with open(configfile) as config:
            cfg = json.load(config)
            config.close()
            return cfg, None
    except Exception as e:
        return None, e


# returns the url for the stage
def get_url(config, stage):
    cfg = config["stage"][stage]
    return cfg["url"]


# returns the account address for the stage
def get_account(config, stage):
    cfg = config["stage"][stage]
    return cfg["account"]


# returns the database file location
def get_db_url(config):
    return config["database"]["url"]


# returns the base directory for contacts
def get_contract_path(config, filename=None):
    if filename:
        return "{}/{}".format(config["contract-dir"], filename)
    return config["contract-dir"]


# returns an xxhash of the passed string
def get_hash(str):
    bs = bytes(str, 'utf-8')
    return xxhash.xxh64(bs).hexdigest()

def display_deployment_rows(rows):
    for row in rows:
        print("{} - {} - {} - {} - {}".format(row["contact-name"], row["hash"], row["address"], row["stage"], row["timestamp"]))
    print("total deployments: {}".format(len(rows)))

def display_contract_rows(rows):
    for row in rows:
        print("{} - {} - {}".format(row['name'], row['hash'], row['timestamp']))
    print("total contracts: {}".format(len(rows)))

