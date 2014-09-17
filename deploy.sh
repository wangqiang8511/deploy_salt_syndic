## Deploy salt
curl -L http://bootstrap.saltstack.com | sudo sh -s -- "$@" -S -M -X git v2014.1.10


git clone https://github.com/wangqiang8511/deploy_salt_syndic.git /tmp/syndic

python /tmp/syndic/prepare_salt_conf.py

sudo mkdir -p /etc/salt/pki
if [ -d /tmp/.saltcloud ];
then
    sudo cp /tmp/.saltcloud/minion.pem /etc/salt/pki/minion.pem
    sudo cp /tmp/.saltcloud/minion.pub /etc/salt/pki/minion.pub
    sudo cp /tmp/.saltcloud/minion /etc/salt/minion
    if [ -e /tmp/.saltcloud/grains ];
    then
    sudo cp /tmp/.saltcloud/grains /etc/salt/grains
    fi
    if [ -e /tmp/.saltcloud/master ];
    then
    sudo cp /tmp/.saltcloud/master /etc/salt/master
    sudo cp /tmp/.saltcloud/autosign.conf /etc/salt/autosign.conf
    sudo service salt-master restart
    sudo salt-syndic -d
    fi
else
    sudo cp /tmp/minion.pem /etc/salt/pki/minion.pem
    sudo cp /tmp/minion.pub /etc/salt/pki/minion.pub
    sudo cp /tmp/minion /etc/salt/minion
    if [ -e /tmp/grains ];
    then
    sudo cp /tmp/grains /etc/salt/grains
    fi
fi

if [ -e /etc/init/salt-minion.conf ];
then
    sudo initctl restart salt-minion
else
    sudo service salt-minion restart
fi
