# Zabbix Template: pyznap ZFS Snapshots

Template for monitoring ZFS snapshots by [yboetz/pyznap](https://github.com/yboetz/pyznap).

* Show the number of snapshots on host & on destination
* Show timestamps of the latest snapshot on host & on destination
* Alert when a snapshot is outstanding
* Alert when a cleaning is inactive

### Requirements

```
apt install python3-pip
pip3 install python-crontab
```

### How to use

1. Download the scripts to `/etc/zabbix/scripts`
2. Copy the User Parameter file to `/etc/zabbix/zabbix_agentd.d`
3. Restart Zabbix-Agent
4. Upload the template to Zabbix Server
5. Link the template to a host

### Screenshots

![](screenshots/items.png)
![](screenshots/triggers.png)
