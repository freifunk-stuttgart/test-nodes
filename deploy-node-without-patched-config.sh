#!/bin/bash
#Parameter:
#1: name: s00-gw01
#2: network ffs-c0000
#3: mac
#4: secret
NAME=$1
NETWORK=$2
MAC=$3
SECRET=$4
GW=$5
REMOTE=$6
PORT=$7
echo Creating $1
virsh destroy $NAME
virsh undefine $NAME
#URL=http://firmware.freifunk-stuttgart.de/gluon/archive/1.3/factory/gluon-ffs-x86-64.img.gz
#URL=http://firmware.freifunk-stuttgart.de/gluon/archive/1.7/factory/gluon-ffs-x86-64.img.gz
#URL=http://firmware.freifunk-stuttgart.de/gluon/archive/1.9%2B2020-06-06/factory/gluon-ffs-x86-64.img.gz
URL=http://[2a01:4f8:190:5205:260:2fff:fe89:3deb]/gluon/stable/factory/gluon-ffs-2.2%2B2021-04-16-g.197e44da-s.c4a01fd-x86-64.img.gz
#URL=http://firmware.freifunk-stuttgart.de/gluon/archive/@leonard/2018-07-09_jenkins-ffs-firmware-185/factory/gluon-ffs-1.4%2B2018-07-09-g.f0103738-s.a21d3bd-x86-64.img.gz
#URL=https://firmware.freifunk-stuttgart.de/gluon/archive/%40leonard/2018-07-09_jenkins-ffs-firmware-186/factory/gluon-ffs-1.5%2B2018-07-09-g.e968a225-s.512b64b-x86-generic.img.gz

echo curl  -s $URL 
curl  -s $URL | gunzip  > /var/lib/libvirt/images/$NAME.img
#truncate -s 1G /var/lib/libvirt/images/$NAME.img
#virsh net-create networks/ffs-nodes
virsh net-create networks/$NETWORK
virsh net-create networks/ffs-clients
#set -e 
ifconfig $NETWORK:0 192.168.1.100
echo virt-install --name $NAME --ram 64 -f /var/lib/libvirt/images/$NAME.img,device=disk --noautoconsole --network network=$NETWORK,model=virtio,mac=$MAC --network network=ffs-nodes,model=virtio --os-variant virtio26 --import
virt-install --name $NAME --ram 128 -f /var/lib/libvirt/images/$NAME.img,device=disk --noautoconsole --network network=$NETWORK,model=virtio,mac=$MAC --network network=default,model=virtio --os-variant auto --import

sleep 30
expect << EOF
spawn virsh console ffs-PoldyTestKvmroot-s28gw01n03
expect -re ".*]"
send "\n\r"
expect -re ".*#"
send "echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5jQU6UhGFfeQrEZ09cNjyFuOrOKZxslGGznblcr/SSjHGCtISk9Z4bGquMAuqcn4hd6xlT+SyRJaIivkAWFfzpUKFDtg4MyE47s82Ny0ZGHvP+I4BVQsjdwYFKZLK9iqmkqZ52YrgSSjbH1QKKHDqvYx97X2hZUDx96lNzQrZAxzr21UEIqxGTXjcrhCDy+g81gyHQLnPc/RgU28JKEtmm1yOWrlLyN5ylmmGrexyY2fo4asJIJ60+KWjbID7I0VDcCHV2g6GOkQBgBoY6VIX+3ipX3nN8ANdB24Vjf9906Vc+FQowQAFW/NxLRS6bS6LqwskTdkf2RHbPykuBrAl root@leela.selfhosted.de' > /etc/dropbear/authorized_keys\n\r"
expect -re ".*#"
send "/etc/init.d/dropbear restart\n\r"
expect -re ".*#"
send "echo done\n"
EOF

sleep 3
SSH="ssh -q -F ssh-config gluon-setup"
$SSH uci set fastd.mesh_vpn.secret=$SECRET
$SSH uci set gluon-setup-mode.@setup_mode[0].enabled='0'
$SSH uci set gluon-setup-mode.@setup_mode[0].configured='1'
$SSH uci commit gluon-setup-mode
$SSH uci set system.@system[0].hostname=$NAME
$SSH uci commit fastd
$SSH uci commit system
$SSH /etc/init.d/system reload
#$SSH opkg update
#$SSH opkg install mtr
$SSH reboot
echo undoing: 
echo ifconfig $NETWORK:0 192.168.1.100
ifconfig $NETWORK:0 down


