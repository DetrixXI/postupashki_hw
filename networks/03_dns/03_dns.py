import ipaddress
import random
import socket
import sys
import time

RCODE_NAMES = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 5: "REFUSED"}

TYPE_CODES = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16, "AAAA": 28}
TYPE_NAMES = {code: name for name, code in TYPE_CODES.items()}


def encode_name(name):
    """берем имя, вставляем длины для каждой метки (секции) (однобайтовый указатель)"""
    out = b""
    for label in (p for p in name.split(".")):
        raw = label.encode("ascii")
        out += bytes([len(raw)]) + raw
    # дополняем нулевым байтом - конец имени
    return out + b"\x00"


def build_query(qname, qtype):
    """собираем пакет и возвращаем id запроса, пакет """
    qid = random.getrandbits(16)
    # заголовок из 12 байт
    # id для сверки, 0x0100 - бит рекурсии и нули, 
    # кол-во вопросов (1 шт.), все остальное 0 т.к. разделов ответа нет в вопросе
    header = (qid.to_bytes(2, "big") + b"\x01\x00" + b"\x00\x01" + b"\x00\x00\x00\x00\x00\x00")
    # сам вопрос - имя это наш id, код, класс IN 
    question = (encode_name(qname) + TYPE_CODES[qtype].to_bytes(2, "big") + b"\x00\x01")
    return qid, header + question


def read_name(msg, offset):
    """читаем доменное имя, с учетом смещения + разворачиваем сжатие"""
    labels = []
    # это смещение, на котором заканчивается имя
    end = None
    pos = offset
    while True:
        length = msg[pos]

        # если байт длины 0, то это конец имени
        if length == 0:
            pos += 1
            # записываем end только если указателей ешще не было,
            # т.е. имя лежит без сжатия целиком подряд - значит конец в исходном месте
            # иначе - end уже установлен и мы его не трогаем 
            if end is None:
                end = pos
            break

        # если 2 старших бита 11, то это указатель,
        # а оставшиеся 14 бит - смещение от начала сообщения
        if length & 0xC0 == 0xC0:
            # фиксируем end 1 раз, 
            if end is None:
                end = pos + 2
            # сборка 14битового смещения - два старших бита зануляем, оставшиеся 6 бит становятся
            # старшими в байте, потом добавляем второй байт сообщения 
            pos = ((length & 0x3F) << 8) | msg[pos + 1]
            continue

        # берем байты метки без байта длины
        labels.append(msg[pos + 1 : pos + 1 + length])
        pos += 1 + length

    # в итоге собираем все вместе
    return ".".join(el.decode("ascii") for el in labels) + ".", end


def format_rdata(msg, rtype, rdata, rdata_off):
    """msg = ответ весь, rtype = код типа записи, rdata = срез данных записи, rdata_off = смещение rdata"""
    # код А
    if rtype == 1:
        return ".".join(str(b) for b in rdata)

    # АААА
    if rtype == 28:
        # надеюсь, стандартными библиотеками пользоваться можно?))
        return str(ipaddress.IPv6Address(rdata))

    # CNAME и NS
    if rtype in (2, 5):
        name, _ = read_name(msg, rdata_off)
        return name

    # MX
    if rtype == 15:
        pref = int.from_bytes(rdata[:2], "big")
        name, _ = read_name(msg, rdata_off + 2)
        return f"{pref} {name}"

    # TXT
    if rtype == 16:
        parts = []
        i = 0
        while i < len(rdata):
            # читаем тут длины строк, потом добавляем их в parts
            lng = rdata[i]
            parts.append(rdata[i + 1:i + 1 + lng])
            i += 1 + lng
        return b"".join(parts).decode("ascii")


def parse_response(msg):
    """возвращает qid, rcode, records"""

    qid = int.from_bytes(msg[0:2], "big")
    # 4ый байт - тут флаги AA, TC, RA и т.д.(первые 4 бита) и код (оставшиеся 4 бита)
    # т.к. нужен только код - зануляем старшие биты
    rcode = msg[3] & 0x0F
    # счеичмкм разделов - сколько вопросов, сколько ответов
    qdcount = int.from_bytes(msg[4:6], "big")
    ancount = int.from_bytes(msg[6:8], "big")
    off = 12
    # раздел вопросов пропускаем
    for _ in range(qdcount):  
        _, off = read_name(msg, off)
        # qtype и qclass пропускаем 
        off += 4

    # раздел вопросов
    records = []
    for _ in range(ancount):
        _, off = read_name(msg, off)
        rtype = int.from_bytes(msg[off:off + 2], "big")
        ttl = int.from_bytes(msg[off + 4:off + 8], "big")
        rdlen = int.from_bytes(msg[off + 8:off + 10], "big")
        # начало данных, пропуская заголовок
        off += 10
        # msg[] - срез для А, АААА, TXT; смещение для cname, ns, mx
        records.append((rtype, ttl, msg[off:off + rdlen], off))
        # и переходим к следующей записи
        off += rdlen
    return qid, rcode, records


def open_socket(ip, port):
    # здесь просто смотрим, какой у нас ip - можно было не парсить ручками ?
    try:
        socket.inet_pton(socket.AF_INET, ip)
        family = socket.AF_INET
    except:
        socket.inet_pton(socket.AF_INET6, ip)
        family = socket.AF_INET6
    # создаем соотв. ip сокет
    sock = socket.socket(family, socket.SOCK_DGRAM)
    sock.connect((ip, port))
    return sock


def receive_response(sock, qid):
    """ждет ответ с нужным id не больше 5 секунд"""
    deadline = time.monotonic() + 2
    while True:
        if deadline - time.monotonic() <= 0:
            return None
        sock.settimeout(deadline - time.monotonic())
        # принимаем датаграмму
        try:
            # данные берем, адрес отправителя не нужен, макс. размер UDP 65535
            data, _ = sock.recvfrom(65535)
        except socket.timeout:
            return None

        # если не совпал идентификатор - ждем дальше
        if int.from_bytes(data[:2], "big") != qid:
            continue
        
        return data 


def main():
    server, port = sys.argv[1], int(sys.argv[2])
    sock = open_socket(server, port)
    cache = {}

    for line in sys.stdin: 
        if not line:
            continue

        qname, qtype_raw = line.strip().rsplit(' ')
        print(f"query {qname} {qtype_raw}")

        qtype = qtype_raw.upper()
        key = (qname.lower(), qtype)

        # если в кеше что то есть и оно актуальное пока что
        now = time.monotonic()
        if key in cache:
            entries, expire = cache[key]
            if now < expire:
                print("status NOERROR")
                for rtype, value, ttl in entries:
                    print(f"answer {rtype} {value} {ttl}")
                print("end")
                continue
            else: 
                del cache[key]

        # в кеше ничего не нашлось (или оно просрочено)
        qid, packet = build_query(qname, qtype)
           
        sock.send(packet)
        data = receive_response(sock, qid)

        if data is None:
            print("status TIMEOUT")
            print("end")
            sys.exit(1)


        _, rcode, records = parse_response(data)
        print(f"status {RCODE_NAMES.get(rcode)}")


        answers = []

        if rcode == 0:
            for rtype, ttl, rdata, rdata_off in records:
                rname = TYPE_NAMES.get(rtype)
                if rname is None:
                    continue
                value = format_rdata(data, rtype, rdata, rdata_off)
                if value is None:
                    continue
                answers.append((rname, value, ttl))
                print(f"answer {rname} {value} {ttl}")

            # тут кешируем, есть какие то данные
            if answers:
                min_ttl = min(ttl for _, _, ttl in answers)
                if min_ttl > 0:
                    cache[key] = (list(answers), time.monotonic() + min_ttl)
        print("end")


if __name__ == "__main__":
    main()
