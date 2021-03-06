## Deploy salt
curl -L http://bootstrap.saltstack.com | sudo sh -s -- "$@" -S -M -X git v2014.1.10

sudo aws s3 cp s3://bigdata-keys/razer-bigdata-deploy.pem /root/.ssh/razer-bigdata-deploy.pem

sudo cat << EOF > /root/.ssh/config
Host bitbucket.org
    HostName bitbucket.com
    User git 
    IdentityFile /root/.ssh/razer-bigdata-deploy.pem
EOF

sudo chmod 0600 /root/.ssh/config 
sudo chmod 0600 /root/.ssh/razer-bigdata-deploy.pem

sudo cat << EOF >> /etc/ssh/ssh_config
StrictHostKeyChecking no
EOF

git clone git@bitbucket.org:razerbigdata/deploy_salt_syndic.git

saltcloudfolder=/tmp/`ls /tmp/ -a | grep .saltcloud`
python /tmp/syndic/prepare_salt_conf.py $saltcloudfolder

sudo rm -rf /etc/salt/pki
sudo mkdir -p /etc/salt/pki/minion
sudo aws s3 cp s3://bigdata-keys/razer_bigdata_salt.pem /etc/salt/pki/minion/minion.pem
sudo aws s3 cp s3://bigdata-keys/razer_bigdata_salt.pub /etc/salt/pki/minion/minion.pub
if [ -d $saltcloudfolder ];
then
    sudo cp $saltcloudfolder/minion /etc/salt/minion
    if [ -e $saltcloudfolder/grains ];
    then
    sudo cp $saltcloudfolder/grains /etc/salt/grains
    fi
    if [ -e $saltcloudfolder/master ];
    then
    sudo cp $saltcloudfolder/master /etc/salt/master
    sudo cp $saltcloudfolder/autosign.conf /etc/salt/autosign.conf
    sudo service salt-master restart
    sudo salt-syndic -d
    fi
else
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
