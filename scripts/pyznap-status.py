import os
import sys
import logging
import json

from datetime import datetime
from configparser import (ConfigParser, NoOptionError, MissingSectionHeaderError,
                          DuplicateSectionError, DuplicateOptionError)
from pkg_resources import resource_string

import pyznap.pyzfs as zfs
from pyznap.process import DatasetBusyError, DatasetNotFoundError

DIRNAME = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = '/etc/pyznap/pyznap.conf'

# How to Use
def help():
    return("""
            Pyznap Monitoring
            https://github.com/sebastian13/zabbix-template-pyznap

            Usage:
                python3 pyznap-status.py [function] [arguments]

            Available [functions]:
                - count [filesystem] [frequency]
                - latest [filesystem]

            """)

def count_snapshots(fsname,snap_freq):
    logger = logging.getLogger(__name__)
    # logger.debug('Cleaning snapshots on {}...'.format(filesystem))

    snapshots = {'frequent': [], 'hourly': [], 'daily': [], 'weekly': [], 'monthly': [], 'yearly': []}

    ssh = None
    children = zfs.find(path=fsname, types=['filesystem', 'volume'], ssh=ssh)

    fs_snapshots = children[0].snapshots()
    
    # catch exception if dataset was destroyed since pyznap was started
    try:
        fs_snapshots = children[0].snapshots()
    except (DatasetNotFoundError, DatasetBusyError) as err:
        logger.error('Error while opening {}: {}...'.format(filesystem, err))
        return 1

    # categorize snapshots
    for snap in fs_snapshots:
        # Ignore snapshots not taken with pyznap or sanoid
        if not snap.name.split('@')[1].startswith(('pyznap', 'autosnap')):
            continue
        try:
            snap_type = snap.name.split('_')[-1]
            snapshots[snap_type].append(snap)
        except (ValueError, KeyError):
            continue

    # Reverse sort by time taken
    for snaps in snapshots.values():
        snaps.reverse()
        #print(snaps)

    # Count all snapshots
    if snap_freq == "total":
        total = snapshots.values()
        total_length = sum(len(row) for row in snapshots.values())
        return(total_length)

    else:
        # Count snapshots of a specific frequency (frequent, hourly, daily, ...)
        count = len(snapshots[snap_freq]) 
        return(count)

    for snap in snapshots[snap_freq]:
        return(snap)

def latest_snapshots(fsname):
    logger = logging.getLogger(__name__)
    # logger.debug('Cleaning snapshots on {}...'.format(filesystem))

    snapshots = {'frequent': [], 'hourly': [], 'daily': [], 'weekly': [], 'monthly': [], 'yearly': []}
    # catch exception if dataset was destroyed since pyznap was started
    #try

    ssh = None
    children = zfs.find(path=fsname, types=['filesystem', 'volume'], ssh=ssh)

    fs_snapshots = children[0].snapshots()
    
    #except (DatasetNotFoundError, DatasetBusyError) as err
    #except as err:
    #    logger.error('Error while opening {}: {}...'.format(filesystem, err))
    #    return 1

    #from pprint import pprint
    #pprint(fs_snapshots)

    # Ignore snapshots not taken with pyznap or sanoid
    for snap in fs_snapshots[:]: # make a copy of fs_snapshots
        if not snap.name.split('@')[1].startswith(('pyznap', 'autosnap')): 
            fs_snapshots.remove(snap)

    #pprint(fs_snapshots)

    latest = str(fs_snapshots[-1])

    import subprocess
    command = str("zfs get -Hpo value creation " + latest)
    data = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    stdout, stderr = data.communicate()
    return int(stdout)

if __name__ == '__main__':
    if (sys.argv[1] == "count" and len(sys.argv) == 4):
        print(count_snapshots(sys.argv[2], sys.argv[3]))
    elif (sys.argv[1] == "latest" and len(sys.argv) == 3):
        print(latest_snapshots(sys.argv[2]))
    else:
        print("""
            [ERROR] Function > """ + sys.argv[1] + """ < is unknown,
                    or the wrong number of arguments was passed.
            """)
        print(help())
        sys.exit(1)
