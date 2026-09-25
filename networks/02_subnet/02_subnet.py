import sys

def to_print(data: dict):
    for key, value in data.items():
        print(f"{key} {value}") 

def ip_to_int(ip:str) -> int:
    ip = ip.split('.')
    return int(ip[0]) << 24 | int(ip[1]) << 16 | int(ip[2]) << 8 | int(ip[3])

def int_to_ip(ip_int: int) -> str:
    ip = f'{((ip_int >> 24) & 255)}.{((ip_int >> 16) & 255)}.{((ip_int >> 8) & 255)}.{((ip_int) & 255)}'
    return ip

def validate_ip_n_pref(ip: str, pref: int):
    for num in map(int, ip.split('.')):
        if num > 255:
            raise ValueError
    if pref > 32:
        print('Длина префикса некорректна', file=sys.stderr)
        sys.exit(1)

def subnet(raw):
    ip, pref = raw.split('/')
    pref = int(pref)
    # validate_ip_n_pref(ip, pref)
    
    ip = ip_to_int(ip)
    mask = (0xFFFFFFFF << (32 - pref)) & 0xFFFFFFFF

    subnet_data['network'] = int_to_ip(ip & mask)
    subnet_data['prefix'] = pref       
    
    if pref == 31:
        subnet_data['broadcast'] = 'none'
        subnet_data['hosts'] = 2
        subnet_data['first'] = subnet_data['network']
        subnet_data['last'] = int_to_ip((ip & mask) + 1)
        subnet_data['netmask'] = int_to_ip(mask)

    elif pref == 32:
        subnet_data['first'] = subnet_data['network']
        subnet_data['last'] = subnet_data['network']
        subnet_data['broadcast'] = 'none'
        subnet_data['hosts'] = 1
        subnet_data['netmask'] = int_to_ip(mask)

    elif pref == 0:
        subnet_data['netmask'] = '0.0.0.0'
        subnet_data['network'] = '0.0.0.0'
        subnet_data['broadcast'] = '255.255.255.255'
        subnet_data['hosts'] = 0xFFFFFFFF - 1
        subnet_data['first'] = int_to_ip((ip_to_int(subnet_data['network'])) | (1 >> 32) + 1)
        subnet_data['last'] = int_to_ip((ip_to_int(subnet_data['network'])) |  (~mask & 0xFFFFFFFF) - 1)

    else:     
        subnet_data['broadcast'] = int_to_ip((ip & mask) | ~mask & 0xFFFFFFFF) if pref is not None else 'none'
        subnet_data['netmask'] = int_to_ip(mask)
        subnet_data['first'] = int_to_ip((ip & mask) | (1 >> 32) + 1)
        subnet_data['last'] = int_to_ip((ip & mask) |  (~mask & 0xFFFFFFFF) - 1)
        subnet_data['hosts'] = ~mask & 0xFFFFFFFF - 1

    to_print(subnet_data)
    ...

def route(tablename, adr):
    with open("process_debug.log", "a", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f
        print('+======')

        table = dict()
        with open(tablename, 'r') as f:
            f = list(map(lambda el: el.strip().split(), f.readlines()))
            for el in f:
                print(el)
                if el == [] or el[0] == '#':
                    continue
                ip, pref = el[0].split('/')
                table[ip] = [pref, el[1]]

            print(table)
            

    ...

subnet_data = {
    'network': None,
    'broadcast': None,
    'netmask': None,
    'prefix': None,
    'first': None,
    'last': None,
    'hosts': None
}

op_mode = {
    'subnet': subnet,
    'route': route
}


line = sys.argv[1:]
op_mode[line[0]](*line[1:])
