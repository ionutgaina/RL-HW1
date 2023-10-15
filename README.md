Scheleton for the Hub implementation.

## Running

```bash
sudo python3 checker/topo.py
```

This will open 9 terminals, 6 hosts and 3 for the switches. On the switch terminal you will run 

```bash
make run_witch
```

The hosts have the following IP addresses.
```
host0 192.168.1.0
host1 192.168.1.1
host2 192.168.1.2
host3 192.168.1.3
host4 192.168.1.4
host5 192.168.1.5
host6 192.168.1.6
```

We will be testing using the ICMP. For example, from host0 we will run:

```
ping 192.168.1.2
```

Note: We will use wireshark for debugging. From any terminal you can run `wireshark&`.
