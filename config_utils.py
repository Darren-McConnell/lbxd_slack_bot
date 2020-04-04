import json
import pathlib

def config_path():
    basedir = pathlib.Path(__file__).resolve().parent
    return basedir.joinpath('users.json')

def get_user_config():
    with open(config_path()) as config:
        user_dict = json.load(config)
    return user_dict

def get_active_users():
    return list(get_user_config().keys())

def write_config(config_json):
    with open(config_path(), 'w') as config:
        json.dump(config_json, config, indent=4)

def set_config_value(username, field, value):
    user_config = get_user_config()
    user_config[username][field] = value 
    write_config(user_config)