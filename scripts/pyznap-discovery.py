import os
import sys
import logging
import json
import re
import datetime
from crontab import CronTab
from configparser import (ConfigParser, NoOptionError, MissingSectionHeaderError,
                          DuplicateSectionError, DuplicateOptionError)
from pkg_resources import resource_string

DIRNAME = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = '/etc/pyznap/pyznap.conf'
CRON = '/etc/cron.d/pyznap'

# How to Use
def help():
    return("""
            Pyznap Monitoring
            https://github.com/sebastian13/zabbix-template-pyznap
            Usage:
                python3 pyznap-discovery.py
            """)

def read_config(path):
    logger = logging.getLogger(__name__)

    if not os.path.isfile(path):
        logger.error('Error while loading config: File {:s} does not exist.'.format(path))
        return None

    parser = ConfigParser()
    try:
        parser.read(path)
    except (MissingSectionHeaderError, DuplicateSectionError, DuplicateOptionError) as e:
        logger.error('Error while loading config: {}'.format(e))
        return None

    config = []
    options = ['key', 'frequent', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'snap', 'clean',
               'dest', 'dest_keys', 'compress', 'exclude', 'raw_send']

    for section in parser.sections():
        dic = {}
        config.append(dic)
        dic["{#NAME}"] = section

        for option in options:
            try:
                value = parser.get(section, option)
            except NoOptionError:
                dic[option] = None
            else:
                if option in ['key']:
                    dic[option] = value if os.path.isfile(value) else None
                elif option in ['frequent', 'hourly', 'daily', 'weekly', 'monthly', 'yearly']:
                    dic[option] = int(value)
                elif option in ['snap', 'clean']:
                    dic[option] = {'yes': True, 'no': False}.get(value.lower(), None)
                elif option in ['dest', 'compress']:
                    dic[option] = [i.strip() for i in value.split(',')]
                elif option in ['dest_keys']:
                    dic[option] = [i.strip() if os.path.isfile(i.strip()) else None
                                   for i in value.split(',')]
                elif option in ['exclude']:
                    dic[option] = [[i.strip() for i in s.strip().split(' ')] if s.strip() else None
                                    for s in value.split(',')]
                elif option in ['raw_send']:
                    dic[option] = [{'yes': True, 'no': False}.get(i.strip().lower(), None)
                                   for i in value.split(',')]
    # Pass through values recursively
    for parent in config:
        for child in config:
            if parent == child:
                continue
            child_parent = '/'.join(child["{#NAME}"].split('/')[:-1])  # get parent of child filesystem
            if child_parent.startswith(parent["{#NAME}"]):
                for option in ['key', 'frequent', 'hourly', 'daily', 'weekly', 'monthly', 'yearly',
                               'snap', 'clean']:
                    child[option] = child[option] if child[option] is not None else parent[option]

    mydict = {'{#FUZZYTIME_SNAP}': fuzzytime("snap"),
              '{#FREQUENCY_SNAP}': frequency("snap"),
              '{#FUZZYTIME_SEND}': fuzzytime("send"),
              '{#FREQUENCY_SEND}': frequency("send")}
    
    i = 0
    while i < len(config):
        # Add Fuzzytime and Frequency to each conf
        config[i].update(mydict)

        # Replace ['keys'] with Zabbix compatibel keys
        config[i]['{#CLEAN}'] = config[i].pop('clean')
        config[i]['{#SNAP}'] = config[i].pop('snap')
        config[i]['{#COMPRESS}'] = config[i].pop('compress')
        #config[i]['{#DEST}'] = config[i].pop('dest')
        config[i]['{#DEST_KEYS}'] = config[i].pop('dest_keys')
        config[i]['{#EXCLUDE}'] = config[i].pop('exclude')
        config[i]['{#KEY}'] = config[i].pop('key')
        config[i]['{#RAW_SEND}'] = config[i].pop('raw_send')
        config[i]['{#FREQUENT}'] = config[i].pop('frequent')
        config[i]['{#HOURLY}'] = config[i].pop('hourly')
        config[i]['{#DAILY}'] = config[i].pop('daily')
        config[i]['{#WEEKLY}'] = config[i].pop('weekly')
        config[i]['{#MONTHLY}'] = config[i].pop('monthly')
        config[i]['{#YEARLY}'] = config[i].pop('yearly')

        i += 1

    # Sort by pathname
    config = sorted(config, key=lambda entry: entry["{#NAME}"].split('/'))
    # Print as prettified JSON
    return json.dumps(config, indent=4, sort_keys=True)

# Return the descriptor of a cronjob
def frequency(type):
    cron = CronTab(tabfile=CRON)
    iter = cron.find_command(re.compile("pyznap.*" + type))
    for job in iter:
        return job.description(use_24hour_time_format=True)

# Return the fuzzytime - i.e. the time between each cron run
def fuzzytime(type):
    cron = CronTab(tabfile=CRON)
    iter = cron.find_command(re.compile("pyznap.*" + type))
    for job in iter:
        # Calculate seconds between each execution
        # A default tolerance of 300 seconds will be added via preprocessing on Zabbix Server.
        # This can be customized by overwriting the inherited macro {$FUZZYTOLERANCE}.
        fuzzytime = ( 86400 // job.frequency_per_day() )
        return fuzzytime

if __name__ == '__main__':
  print(read_config(CONFIG_DIR))
