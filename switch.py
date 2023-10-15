#!/usr/bin/python3

import sys
import struct
import wrapper
from wrapper import recv_from_any_link, send_to_link

def parse_ethernet_header(data):
    # Unpack the header fields from the byte array
    dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])

    # Convert MAC addresses to human-readable format
    dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
    src_mac = ':'.join(f'{b:02x}' for b in src_mac)

    vlan_id = None
    # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
    if ether_type == b'\x81\x00':
        vlan_tci = int.from_bytes(frame[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID

    return dest_mac, src_mac, ethertype, vlan_id

def send_bdpu_every_sec():
    while True:
        # TODO Send BDPU every second if necessary
        time.sleep(1)

def main():

    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    interfaces = range(0, wrapper.init(sys.argv[1:]))


    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()

    while True:
        interface, data, length = recv_from_any_link()

        # TODO: Check if this is an Ethernet frame with VLAN tagging (802.1Q)
        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)
        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print(f'EtherType: {ethertype}')
        # TODO: Implement broadcast.
        # TODO: Implement learning
        # TODO: Implement vlan
        # TODO: Implement STP
        print("Received frame of size {} on interface {}".format(length, interface))


        # send_to_link(i, data, length)


if __name__ == "__main__":
    main()
