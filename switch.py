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

def is_unicast(mac: str):
    mac_split = mac.split(':')
    return int(mac_split[0], 16) & 0x01 == 0
    
def is_trunk(interface):
    return interfaces_vlan[get_interface_name(interface)] == "T"

def manage_vlan(interface, data, length, interfaces_vlan, vlan_id):
    # VLAN(sending)
    if(is_trunk(interface)):
        data = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
        length += 4
        send_to_link(interface, data, length)
    else:
        if(int(interfaces_vlan[get_interface_name(interface)]) == vlan_id):
            send_to_link(interface, data, length)
            
def manage_stp(interface):
            if(is_trunk(interface)):
                frame, length = create_stp_frame(root_switch_priority, 0, switch_priority)
                send_to_link(interface, frame, length) 
        
def create_stp_frame(root_bridge_id, root_path_cost, sender_bridge_id):
    bpdu_config = struct.pack('!QQQ', root_bridge_id, root_path_cost, sender_bridge_id)
    bdpu_header = struct.pack('!HBB', 0x0000, 0x00, 0x00)
    llc_header = struct.pack('!3s', b'\x42\x42\x03')
    length = len(bpdu_config) + len(bdpu_header) + len(llc_header)
    ethernet_header = struct.pack('!6s6sH', b'\x01\x80\xc2\x00\x00\x00', get_switch_mac(), length)
    frame = ethernet_header + llc_header + bdpu_header + bpdu_config
    length = len(frame)
    return frame, length
    
def parse_stp_frame(data):
    bdpu_padding = 14 + 4 + 3
    bdpu_config = data[bdpu_padding: bdpu_padding + 24]
    root_bridge_id, root_path_cost, sender_bridge_id = struct.unpack('!QQQ', bdpu_config)
    return root_bridge_id, root_path_cost, sender_bridge_id
            
def send_bdpu_every_sec(interfaces):
    while True:
        if(is_root):
            for i in interfaces:
                manage_stp(i)     
        time.sleep(1)
          
def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]

    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))

    file_path = './configs/switch' + switch_id + '.cfg'
    
    # Read config file
    with open(file_path) as f:
        lines = f.readlines()
    
    # STP config
    global switch_priority 
    switch_priority = int(lines[0].strip())
    global root_switch_priority 
    root_switch_priority = switch_priority
    global root_path_cost
    root_path_cost = 0
    global is_root 
    is_root = True
    global ports
    ports = []
    
    # VLAN config
    global interfaces_vlan
    interfaces_vlan = {}
    

    
    for line in lines[1:]:
        line = line.strip().split(' ')
        interface = line[0]
        vlan = line[1]
        interfaces_vlan[interface] = vlan
        
    
    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec, args=(interfaces,))
    t.start()

    # Printing interface names
    for i in interfaces:
        print(get_interface_name(i))
        
    MAC_TABLE = {}
    
    # STP init
    for i in interfaces:
        if (is_trunk(i)):
            ports[i] = "BLOCKING"

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
            if (ethertype == 0x8100):
                data = remove_vlan_tag(data)
                length -= 4
        else:
            vlan_id = int(interfaces_vlan[get_interface_name(interface)])
            
            
        
        if is_unicast(dest_mac):
            if dest_mac in MAC_TABLE:
                manage_vlan(MAC_TABLE[dest_mac], data, length, interfaces_vlan, vlan_id)
            else:
                for i in interfaces:
                    if i != interface:
                        manage_vlan(i, data, length, interfaces_vlan, vlan_id)
        else:
            if (dest_mac != "01:80:c2:00:00:00"):
                for i in interfaces:
                    if i != interface:
                        manage_vlan(i, data, length, interfaces_vlan, vlan_id)
            else:
                print("STP frame received")
                root_bridge_id, root_path_cost, sender_bridge_id = parse_stp_frame(data)
                print("Root bridge id: " + str(root_bridge_id))
                print("Root path cost: " + str(root_path_cost))
                print("Sender bridge id: " + str(sender_bridge_id))
                
        
        
        if (root_bridge_id == switch_priority):
            for port in ports:
                ports[port] = "DESIGNATED"
                
        # data is of type bytes.
        # send_to_link(i, data, length)

if __name__ == "__main__":
    main()
