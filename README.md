# Test Nodes

These scripts can deploy test nodes (Gluon) and test clients (connected to nodes).

## Usage

### Deploy a node

A node is always a VM running Gluon.

`deploy-node.py`: deploy a node on a given gateway in a given segment.

Example:
```
deploy-node.py -s 32 -g gw09n03
```
Deploys a new node in Segment 32 connected to gateway 9n3.

### Deploy a client

A client is a Container running Debian.

1. Run `mkclientconfig.py`
1. Find the desired line in the output.
1. Execute the line.

e.g.

```
./deploy-client.sh ffs-client-s29gw09n03 2993
```
for a Client in Segment 29, connected to gateway 9n3.

### Add a new gateway or new segments for gateway

When a new gateway is added or a gateway supports a new segment,
`mknodeconfig.py` must be adjusted. It will generate new peer files, which need
to be pushed to `peers-ffs`.

## Installation

```
apt install fastd expect
```

You might to disable fastd-deamon (mask or disable)

Create a config file named after your hostname, i.e. `myhost.conf` if your
hostname is `myhost`.

A `sample.conf` exists that can be used as a template
