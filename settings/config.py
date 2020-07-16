import os
import sys
from configparser import ConfigParser

base_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_path, "settings.ini")

if os.path.exists(config_path):
    cfg = ConfigParser(allow_no_value=True, converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    cfg.read(config_path)
else:
    print("Config not found! Exiting!")
    sys.exit(1)