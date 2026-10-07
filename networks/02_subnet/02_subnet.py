import sys

# print(sys.argv, file=sys.stderr)

def to_print(data: dict):
    for key, value in data.items():
        print(f"{key} {value}") 

def ip_to_int(ip:str) -> int:
    ip = ip.split('.')
    return int(ip[0]) << 24 | int(ip[1]) << 16 | int(ip[2]) << 8 | int(ip[3])

def int_to_ip(ip_int: int) -> str:
    ip = f'{((ip_int >> 24) & 255)}.{((ip_int >> 16) & 255)}.{((ip_int >> 8) & 255)}.{((ip_int) & 255)}'
    return ip

def mask(prefix: int) -> int:
    return (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix else 0

def subnet(raw):
    ip, pref = raw.split('/')
    pref = int(pref)
    
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

def read_routes(path: str):
    routes = []
    with open(path, 'r', encoding='utf-8') as f:
        for _, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = line.split()
            iface = line

            ip, pref = line[0].split('/')
            pref = int(pref) 
            ip = ip_to_int(ip)
            
            routes.append((ip, pref, iface))  
    return routes

def route(table_path, dest_str):
    routes = read_routes(table_path)
    target = ip_to_int(dest_str)
    
    best_prefix = -1 
    best_iface = None
    
    for ip, pref, iface in routes:
        # попадаем вообще в сеть или нет 
        if (target & mask(pref)) == ip:
            
            # чем больше число префикса, тем лучше маршрут
            if pref > best_prefix:
                best_prefix = pref
                best_iface = iface
                
    # формируем вывод
    if best_iface is not None:
        print(f"via {best_iface[1]}\nprefix {best_prefix}")
    else:
        print("unreachable true")
        sys.exit(1)


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
