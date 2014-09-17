#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import time
import yaml
import json
import urllib
import urllib2
import httplib
import commands


syndic_master_data = {
    "log_level": "info",
    "fileserver_backend": ["git", "roots"],
    "gitfs_remotes": [],
    "ext_pillar": [],
    "autosign_file": "/etc/salt/autosign.conf",
    "syndic_master": "10.17.0.10",
    "syndic_log_file": "/var/log/salt/syndic",
    "syndic_pidfile": "/var/run/salt-syndic.pid",
}

syndic_minion_data = {
    "log_level": "info",
}

config = {
    'tmp_cloud_folder': "/tmp/.saltcloud/"
}


def etcd_get(key):
    conn = httplib.HTTPConnection("10.17.0.10", 4001)
    conn.request("GET", "/v2/keys/" + key)
    rep = conn.getresponse()
    if rep.status == 200:
        return json.loads(rep.read())
    return {}


def etcd_put(key, value):
    params = {"value": value}
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request('http://10.17.0.10:4001/v2/keys/' + key, data=urllib.urlencode(params))
    request.get_method = lambda: 'PUT'
    rep = opener.open(request)
    if rep.code == 200 or rep.code == 201:
        return True
    return False


def load_grains():
    grains_file = os.path.join(config["tmp_cloud_folder"], "grains")
    if os.path.isfile(grains_file):
        stream = open(grains_file, 'r')
        return yaml.load(stream)
    return {}


def load_minion():
    minion_file = os.path.join(config["tmp_cloud_folder"], "minion")
    if os.path.isfile(minion_file):
        stream = open(minion_file, 'r')
        return yaml.load(stream)
    return {}


def get_roles():
    return load_grains().get("roles", {})


def is_syndic_master():
    salt_role = get_roles().get("salt", "")
    return salt_role == "syndic_master"


def is_syndic_minion():
    salt_role = get_roles().get("salt", "")
    return salt_role == "syndic_minion"


def get_current_ip():
    intf = 'eth0'
    intf_ip = commands.getoutput("ip address show dev " + intf).split()
    intf_ip = intf_ip[intf_ip.index('inet') + 1].split('/')[0]
    return intf_ip


def get_id():
    return load_minion().get("id", "")


def get_domain():
    id = get_id()
    if not id:
        return ""
    split_names = id.split(".")
    if len(split_names) < 2:
        return ""
    return ".".join(split_names[1:])


def get_syndic_master():
    domain = get_domain()
    key = "salt/syndic_master/" + domain
    return etcd_get(key).get("node", {}).get("value", "")


def set_syndic_master():
    myip = get_current_ip()
    domain = get_domain()
    key = "salt/syndic_master/" + domain
    return etcd_put(key, myip)


def render_syndic_master_template():
    gitfs_remotes = load_grains().get("salt", {}).get("gitfs_remotes", [])
    ext_pillar = load_grains().get("salt", {}).get("ext_pillar", [])
    syndic_master_data["gitfs_remotes"] = gitfs_remotes
    syndic_master_data["ext_pillar"] = ext_pillar
    master_file = os.path.join(config["tmp_cloud_folder"], "master")
    yaml.dump(syndic_master_data, open(master_file, "w"),
              default_flow_style=False, indent=2)
    pass


def render_autosign_file():
    autosign_file = os.path.join(config["tmp_cloud_folder"], "autosign.conf")
    with open(autosign_file, "w") as f:
        f.write("*." + get_domain())
    pass


def render_minon_template():
    minion_file = os.path.join(config["tmp_cloud_folder"], "minion")
    syndic_minion_data["id"] = get_id()
    syndic_minion_data["master"] = str(get_syndic_master())
    if not syndic_minion_data["master"]:
        return False
    yaml.dump(syndic_minion_data, open(minion_file, "w"),
              default_flow_style=False, indent=2)
    return True


def prepare_conf():
    if is_syndic_master():
        set_syndic_master()
        render_syndic_master_template()
        render_autosign_file()
        render_minon_template()
        return
    if is_syndic_minion():
        c = 0
        while  c < 10:
            if render_minon_template():
                return
            c += 1
            time.sleep(20)
        return
    return


if __name__ == "__main__":
    import sys
    config["tmp_cloud_folder"] = sys.argv[1]
    prepare_conf()
