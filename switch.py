#!/usr/bin/python3

import sys
import struct
import wrapper
from wrapper import recv_from_any_link, send_to_link

def parse_ethernet_header(data):
    # Unpack the header fields from the byte array
    #dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])
    dest_mac = data[0:6]
    src_mac = data[6:12]
    
    # Extract ethertype. Under 802.1Q, this may be the bytes from the VLAN TAG
    ethertype = (data[12] << 8) + data[13]

    vlan_id = None
    # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
    if ether_type == b'\x81\x00':
        vlan_tci = int.from_bytes(frame[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID
        ethertype = (frame[16] << 8) + frame[17]

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
        # Note that data is of type bytes([...]).
        # b1 = bytes([72, 101, 108, 108, 111])  # "Hello"
        # b2 = bytes([32, 87, 111, 114, 108, 100])  # " World"
        # b3 = b1[0:2] + b[3:4].
        interface, data, length = recv_from_any_link()

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

        # Print the MAC src and MAC dst in human readable format
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)

        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print(f'EtherType: {ethertype}')

        print("Received frame of size {} on interface {}".format(length, interface))

        # TODO: Implement forwarding with learning
        # TODO: Implement VLAN support
        # TODO: Implement STP support
        
        # data is of type bytes.
        # send_to_link(i, data, length)


if __name__ == "__main__":
    main()
