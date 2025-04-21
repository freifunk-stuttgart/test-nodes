#!/bin/bash
set -eu

NAME="${1:-}"
ID="${2:-}"

if [ -z "$NAME" ] || [ -z "$ID" ]; then
	echo usage: $0 NAME ID
	echo Tip: run mkclientconfig.py to generate a commandline for this script
	exit 1
fi

VMID=9$ID
source `hostname`.conf
pct stop $VMID || true
pct destroy $VMID || true
pct create $VMID $CT_TEMPLATE --features nesting=1 --storage ${ZP} \
	--net0 name=eth0,bridge=${BR_CLIENT},ip=dhcp,ip6=auto,tag=$ID,type=veth \
	--memory 512 --hostname $NAME
pct start $VMID

