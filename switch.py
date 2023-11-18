#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

def parse_ethernet_header(data):
    # Unpack the header fields from the byte array
    #dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])
    dest_mac = data[0:6]
    src_mac = data[6:12]
    
    # Extract ethertype. Under 802.1Q, this may be the bytes from the VLAN TAG
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
    if ether_type == 0x8200:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    # 0x8100 for the Ethertype for 802.1Q
    # vlan_id & 0x0FFF ensures that only the last 12 bits are used
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def remove_vlan_tag(data):
    return data[0:12] + data[16:]

def send_bdpu_every_sec():
    while True:
        # TODO Send BDPU every second if necessary
        time.sleep(1)

def is_unicast(mac: str):
    mac_split = mac.split(':')
    return int(mac_split[0], 16) & 0x01 == 0
    
def is_trunk(interface_list, interface):
    print("GET INTERFACE NAME: " + get_interface_name(interface))
    print("GET INTERFACE LIST: " + str(interface_list))
    print("GET INTERFACE VLAN: " + str(interface_list[get_interface_name(interface)]))
    return interface_list[get_interface_name(interface)] == "T"

def manage_vlan(interface, data, length, interfaces_vlan, vlan_id):
    # VLAN(sending)
    if(is_trunk(interfaces_vlan, interface)):
        data = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
        length += 4
        print("Added VLAN tag to send")
        send_to_link(interface, data, length)
    else:
        if(int(interfaces_vlan[get_interface_name(interface)]) == vlan_id):
            print("Same VLAN send")
            send_to_link(interface, data, length)
        else:
            print("Different VLAN send" + str(interfaces_vlan[get_interface_name(interface)]) + " " + str(vlan_id))
            

def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]

    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))

    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()

    # Printing interface names
    for i in interfaces:
        print(get_interface_name(i))
        
    file_path = './configs/switch' + switch_id + '.cfg'
    
    # Read config file
    with open(file_path) as f:
        lines = f.readlines()
    
    switch_priority = int(lines[0].strip())
    
    print("Switch priority: " + str(switch_priority))
    
    interfaces_vlan = {}
    
    for line in lines[1:]:
        line = line.strip().split(' ')
        interface = line[0]
        vlan = line[1]
        interfaces_vlan[interface] = vlan
        
    MAC_TABLE = {}

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

        # Note. Adding a VLAN tag can be as easy as
        # tagged_frame = data[0:12] + create_vlan_tag(10) + data[12:]

        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print(f'EtherType: {ethertype}')

        print("Received frame of size {} on interface {}".format(length, interface), flush=True)

        MAC_TABLE[src_mac] = interface
        
        # VLAN(receiving)
        if interfaces_vlan[get_interface_name(interface)] == "T":
            data = remove_vlan_tag(data)
            length -= 4
            print("Removed VLAN tag")
        else:
            vlan_id = int(interfaces_vlan[get_interface_name(interface)])
            print("GET VLAN ID: " + str(vlan_id))
            
            
        
        if is_unicast(dest_mac):
            if dest_mac in MAC_TABLE:
                manage_vlan(MAC_TABLE[dest_mac], data, length, interfaces_vlan, vlan_id)
            else:
                for i in interfaces:
                    if i != interface:
                        manage_vlan(i, data, length, interfaces_vlan, vlan_id)
        else:
            for i in interfaces:
                if i != interface:
                    manage_vlan(i, data, length, interfaces_vlan, vlan_id)
        


        # TODO: Implement VLAN support
        # TODO: Implement STP support

        # data is of type bytes.
        # send_to_link(i, data, length)

if __name__ == "__main__":
    main()
