import ConfigParser

def get_db_config(filename):
    config = ConfigParser.RawConfigParser()
    config.read(filename)
    db = 'database'
    return (config.get(db, 'username'),
            config.get(db, 'password'),
            config.get(db, 'dbname'))
