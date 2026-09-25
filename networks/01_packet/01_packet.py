import sys

def output(data: dict):
    for key, value in data.items():
        if value == None:
            continue
        print(f"{key} {value}")

def IPv4_flags_n_offset(IPv4_lvl_frame):
    flags_raw = int.from_bytes(bytes.fromhex(IPv4_lvl_frame)[6:8], 'big')

    R_flag = flags_raw >> 15 & 1
    if R_flag != 0:
        raise ValueError
    DF_flag, MF_flag, frag_offset = flags_raw >> 14 & 1, flags_raw >> 13 & 1, (flags_raw & 0x0FFF) * 8
    res = []
    if DF_flag == 1:
        res.append('DF')
    if MF_flag == 1:
        res.append("MF")
    if flags_raw:
        IPv4_lvl["ip.flags"] = ','.join(res)

    IPv4_lvl['ip.frag_offset'] = frag_offset

def IPv4_check_sum(IPv4_bytes):
    res = 0
    for ind in range(0, len(IPv4_bytes), 2):
        if ind == 10:
            continue
        res += int.from_bytes(IPv4_bytes[ind:ind+2], 'big')
        if res > 0xFFFF:
            res = (res & 0xFFFF) + 1

    return (~res) & 0xFFFF

def TCP_flags(tcp_b1, tcp_b2):
    flags = {
        "FIN":  bool((tcp_b2 >> 0) & 1),
        "SYN":  bool((tcp_b2 >> 1) & 1),
        "RST":  bool((tcp_b2 >> 2) & 1),
        "PSH":  bool((tcp_b2 >> 3) & 1),
        "ACK":  bool((tcp_b2 >> 4) & 1),
        "URG":  bool((tcp_b2 >> 5) & 1),
        "ECE":  bool((tcp_b2 >> 6) & 1),
        "CWR":  bool((tcp_b2 >> 7) & 1),
        "NS":   bool((tcp_b1 >> 0) & 1),
    }
    res = []
    for key, value in flags.items():
        if value:
            res.append(key)
    return ','.join(res)

ethernet_lvl = {'eth.dst': None, 'eth.src': None, 'eth.ethertype': None}
IPv4_lvl = {
    "ip.version": None,
    "ip.ihl_bytes": None,
    "ip.total_length": None,
    "ip.id": None,
    "ip.flags": None,
    "ip.frag_offset": None,
    "ip.ttl": None,
    "ip.protocol": None,
    "ip.src": None,
    "ip.dst": None,
    "ip.checksum_valid": None
}

tcp_lvl = {
    "tcp.src_port": None,
    "tcp.dst_port": None,
    "tcp.seq": None,
    "tcp.ack": None,
    "tcp.data_offset_bytes": None,
    "tcp.flags": None,
    "tcp.window": None
}

udp_lvl = {
        "udp.src_port": None,
        "udp.dst_port": None,
        "udp.length": None,
    }

payload = {"payload.length": '0'}

frame = ''.join(list(map(lambda el: el.strip().replace(' ', '').lower(), sys.stdin.readlines())))
# frame ="00005e00530100005e00530208004500003d1c46000078116a40ac10000a08080808cfda003500290000abcd0100000100000000000003777777076578616d706c6503636f6d0000010001"
# frame ="001b213c4d5e0025645d1e220800460000401c4620b940062561c0a80101c0a801029404000000000000000000000000000000000000000000000000000000000000000000000000000000000000"


ethernet_lvl['eth.dst'] = ':'.join([frame[i:i+2] for i in range(0, 12, 2)])
ethernet_lvl['eth.src'] = ':'.join([frame[i:i+2] for i in range(12, 24, 2)])
ethernet_lvl['eth.ethertype'] = '0x' + frame[24:28]

frame = frame[28:]
IPv4_lvl_frame = frame
if ethernet_lvl['eth.ethertype'] == '0x0800':
    IPv4_lvl['ip.version'] = IPv4_lvl_frame[0]
    IPv4_lvl["ip.ihl_bytes"] = int(IPv4_lvl_frame[1]) * 4
    IPv4_bytes = bytes.fromhex(IPv4_lvl_frame)[:int(IPv4_lvl["ip.ihl_bytes"])]
    IPv4_flags_n_offset(IPv4_lvl_frame)
    IPv4_lvl['ip.total_length'] = int.from_bytes(IPv4_bytes[2:4])
    IPv4_lvl["ip.id"] = '0x' + IPv4_lvl_frame[8:12]
    IPv4_lvl['ip.ttl'] = IPv4_bytes[8]
    IPv4_lvl['ip.protocol'] = IPv4_bytes[9]
    IPv4_lvl['ip.src'] = '.'.join([str(IPv4_bytes[i]) for i in range(12,16)])
    IPv4_lvl['ip.dst'] = '.'.join([str(IPv4_bytes[i]) for i in range(16,20)])
    IPv4_lvl['ip.checksum_valid'] = 'true' if int.from_bytes(IPv4_bytes[10:12]) == IPv4_check_sum(IPv4_bytes) else 'false'
    payload['payload.length'] = len(IPv4_lvl_frame[int(IPv4_lvl["ip.ihl_bytes"])*2:]) / 2



if IPv4_lvl['ip.protocol'] == 6:
    TCP_frame = IPv4_lvl_frame[IPv4_lvl["ip.ihl_bytes"]*2:]
    TCP_bytes = bytes.fromhex(frame)[IPv4_lvl["ip.ihl_bytes"]:]
    tcp_lvl['tcp.src_port'] = int.from_bytes(TCP_bytes[0:2])
    tcp_lvl["tcp.dst_port"] = int.from_bytes(TCP_bytes[2:4])
    tcp_lvl["tcp.seq"] = int.from_bytes(TCP_bytes[4:8])
    tcp_lvl["tcp.ack"] = int.from_bytes(TCP_bytes[8:12])
    tcp_lvl["tcp.data_offset_bytes"] = (TCP_bytes[12] >> 4) * 4 
    # нужно ли было разбирать опции в TCP? (насколько понял из задания - нет)
    tcp_lvl["tcp.flags"] = TCP_flags(TCP_bytes[12], TCP_bytes[13])
    tcp_lvl["tcp.window"] = (TCP_bytes[14] << 8) | TCP_bytes[15]
    payload['payload.length'] = IPv4_lvl['ip.total_length'] - tcp_lvl["tcp.data_offset_bytes"] - IPv4_lvl["ip.ihl_bytes"]


if IPv4_lvl['ip.protocol'] == 17:
    UDP_frame = IPv4_lvl_frame[IPv4_lvl["ip.ihl_bytes"]*2:]
    UDP_bytes = bytes.fromhex(UDP_frame)
    udp_lvl["udp.src_port"] = int.from_bytes(UDP_bytes[0:2])
    udp_lvl["udp.dst_port"] = int.from_bytes(UDP_bytes[2:4])
    udp_lvl["udp.length"] = int.from_bytes(UDP_bytes[4:6])
    payload['payload.length'] = udp_lvl["udp.length"] - 8


big_data = {**ethernet_lvl, **IPv4_lvl, **tcp_lvl, **udp_lvl, **payload}
output(big_data)



