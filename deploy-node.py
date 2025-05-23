#!/usr/bin/python3
import argparse
import mknodeconfig
import re
from subprocess import check_call, call
import os
import time
import sys

class NodeDeployer:
    def __init__(self, args):
        #specific for ffs10 - move to config....
        gateway = args.gateway
        segment = args.segment

        zp = "zp_pve"
        br_client = "vmbr1"
        br_internet = "vmbr2"

        instances = mknodeconfig.getInstances()
        try:
            gwn, gwi = self.get_gw(gateway)
        except AttributeError:
            print("Parameter -gw hat illegales Format - erwarte gwXXnYY")
            sys.exit(1)

        segment = segment.zfill(2)
        
        instance = f"s{segment}gw{gwn}n{gwi}"
        try:
            i = instances[instance]
        except KeyError as e:
            print("Kombination Segment/GW ist nicht konfiguriert")
            sys.exit(1)
        
        secret = i["secret"]
        vmid = f'8{i["id"]}'
        name = i["name"]
        port = i["port"]
        gw = i["gw"]
        remote = f'{i["remote"]}.gw.freifunk-stuttgart.de'
        mac = i["mac"]
        vlan = i["id"]

        if args.url == None:
            url = self.get_url()
        else:
            url=self.get_url() 

        self.create_expect_cmdfile(vmid,name,gw, remote, port, secret)
        self.create_vm(vmid, name, mac, br_client, vlan, br_internet,zp,url) 
        os.remove("cmdfile.expect")
        print("Finished, attach to Node:")
        print(f"qm terminal {vmid}")

    def get_gw(self, gateway):
        m = re.search('gw([0-9]{2})n([0-9]{2})',gateway)
        gw = m.group(1)
        instance = m.group(2)
        return(gw,instance)
        #:/#

    def create_expect_cmdfile(self, VMID, NAME, GW, REMOTE, PORT, SECRET):
        content = f'''
set timeout 120
spawn qm terminal {VMID}
expect "The highlighted entry will be executed automatically in"
send "\\r"
expect "Please press Enter to activate this console."
#send "\\r"
#expect "IPv6: ADDRCONF(NETDEV_CHANGE): br-setup: link becomes ready"
#set timeout 1
#expect {{
#        -re "root@ffs-.*:/#" {{ send_error "SUCCESS" }}
#        "root@(none):/#" {{ send "exit\\r"; send_error "NONE DETECTED"; exp_continue}}
#        "Please press Enter to activate this console." {{ send "\\r"; exp_continue}}
#        timeout {{ send "exit\\r"; send_error "TIMEOUT"; exp_continue }}
#}}
#send "logread -l 10\\r"
#expect {{
#        "init complete" {{ send_error "SUCCESS"  }}
#        timeout {{ send "logread -l 10\\r"; exp_continue}}
#}}
set timeout 10
expect {{
        ".*" {{ sleep 1 ; exp_continue}}
        timeout {{ send_error "No ouput for 10 seconds" }}
}}
set timeout 120
send_error "!!!!DEVICE SEEMS TO BE READY!!!!"
send "\\r"
send "\\r"
sleep 1
send "uci set fastd.mesh_vpn.secret={SECRET}\\r"
expect -re ".*#"
send {{uci set gluon-setup-mode.@setup_mode[0].enabled='0'}}
send "\\n"
expect -re ".*#"
send {{uci set gluon-setup-mode.@setup_mode[0].configured='1'}}
send "\\n"
expect -re ".*#"
send "uci commit gluon-setup-mode\\n"
expect -re ".*#"
send {{uci set system.@system[0].hostname={NAME}}}
send "\\n"
expect -re ".*#"
send "uci commit system\\n"
expect -re ".*#"
send "/etc/init.d/system reload\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw01.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw02.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw03.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw04.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw05.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw06.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw07.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw08.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw09.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_gw10.enabled='0'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_{GW}.enabled='1'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone_peer_{GW}.remote=\\'\\"{REMOTE}\\" port {PORT}\\'\\n"
expect -re ".*#"
send "uci set fastd.mesh_vpn_backbone.auto_segment=0\\n"
expect -re ".*#"
send "uci commit fastd\\r"
expect -re ".*#"
send "sync\\r"
expect -re ".*#"
send "reboot\\r"
sleep 1
send_error "FINISHED"
'''
        sys.stdout.flush()
        with open("cmdfile.expect","w") as fp:
            fp.write(content)

    def get_url(self):
        BASE="https://firmware.freifunk-stuttgart.de/gluon"
        VER="2.8+2023-03-05-g.ef8c3707-s.c45671b"
        VER="2.9+2023-05-13-g.adfc0fc6-s.e9d4e0d"
        VER="3.0+2024-01-29-g.e95c5d02-s.827cdfc"
        VER="3.2.1+2024-12-18-g.297f8be7-s.1180dfa"
        return f"{BASE}/archive/{VER}/images/factory/gluon-ffs-{VER}-x86-64.img.gz"
    

    def create_vm(self, VMID, NAME, MAC, BR_CLIENT, VLAN, BR_INTERNET,ZP, URL):
        RAM = 128
        DISKSIZE="1G"

        DEST=f"/tmp/vm-{VMID}-disk-0.raw"
        cmd = f"qm stop {VMID}"
        call(cmd, shell=True)
        cmd = f"qm destroy {VMID} --destroy-unreferenced-disks 1 --purge 1"
        call(cmd, shell=True)
        cmd = f"qm create {VMID} --boot order=scsi0 --cores 1 --memory {RAM} --name {NAME} --net0 virtio={MAC},bridge={BR_CLIENT},tag={VLAN} --net1 virtio,bridge={BR_INTERNET} --ostype l26 --serial0 socket --rng0 source=/dev/urandom"
        check_call(cmd, shell=True)
        cmd = f"curl  -s {URL} | gunzip  > {DEST}"
        call(cmd, shell=True)
        cmd = f"qm importdisk {VMID} {DEST} {ZP}"
        check_call(cmd, shell=True)
        cmd = f"rm {DEST}"
        check_call(cmd, shell=True)
        cmd = f"qm set {VMID} --scsihw virtio-scsi-pci --scsi0 {ZP}:vm-{VMID}-disk-0"
        check_call(cmd, shell=True)
        cmd = f"qm start {VMID}"
        check_call(cmd, shell=True)
        print("Waiting for node boot...")
        print("Attaching to node terminal")
        cmd = "expect cmdfile.expect"
        check_call(cmd, shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy a node')
    parser.add_argument('--segment','-s', dest='segment', action='store', required=True,
                    help='segment the node shall be deployed to)')
    parser.add_argument('--gw','-g', dest='gateway', action='store', required=True,
                    help='gateway the node shall be deployed to, in format gwXXnYY')
    parser.add_argument('--url','-u', dest='url', action='store', required=False,
                    help='Firmware to be used')

    args = parser.parse_args()
    nd = NodeDeployer(args)


