import argparse
import http.client
import random
import socket
import sys
import time
from urllib.parse import urlsplit


RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
IDEMPOTENT_METHODS = {"GET", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE"}


def parse_url(url: str):
    """разбираем адрес"""
    parts = urlsplit(url)
    port = parts.port if parts.port is not None else 80
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return parts.hostname, port, path


def try_attempt(host, port, path, method, headers):
    """одна попытка - новое соединение"""
    conn = http.client.HTTPConnection(host, port, timeout=5)
    try:
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        response.read()  # читаем до конца, иначе сервер может счесть соединение оборванным
        return response.status, response.headers
    finally:
        conn.close()


def describe_exception(exc: Exception):
    """переводим исключение в читаемый вид"""
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, ConnectionRefusedError):
        return "connection refused"
    text = str(exc).strip()
    return text


def parse_retry_pause(headers):
    """переводим из заголовка ответа retry after и возвращаем паузу в мс"""
    value = headers.get("Retry-After")
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return int(value) * 1000
    return None


def main():
    # парсим аргументы из командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    host, port, path = parse_url(args.url)

    method = args.method.upper()
    headers = {}
    # если ключ идемпотентности задан - добавляем в заголовки
    # если ключа вообще нет - не добавляем заголовок
    if args.idempotency_key is not None:
        headers["Idempotency-Key"] = args.idempotency_key

    attempts_done = 0
    last_status = None

    while attempts_done < args.max_attempts:
        attempts_done += 1

        try:
            status, response_headers = try_attempt(host, port, path, method, headers)
        except (OSError, http.client.HTTPException) as exc:
            print(f"attempt {attempts_done} error {describe_exception(exc)}", flush=True)
            last_status = None
            can_retry = True
            retry_after_ms = None
        else:
            last_status = status
            print(f"attempt {attempts_done} status {status}", flush=True)
            can_retry = status in RETRYABLE_STATUSES
            retry_after_ms = parse_retry_pause(response_headers) if can_retry else None

        if not can_retry:
            break
        if attempts_done >= args.max_attempts:
            break
        # т.к. POST не идемпотентен - повторяем только с ключом
        if method not in IDEMPOTENT_METHODS and args.idempotency_key is None:
            break

        # расчетный интервал перед попыткой по формуле n = min(2000, 200 * 2^(n-1))
        if retry_after_ms is not None:
            pause_ms = retry_after_ms
        else:
            interval_ms = min(2000, 200 * (2 ** attempts_done))
            pause_ms = int(random.uniform(0, interval_ms))

        print(f"sleep_ms {pause_ms}", flush=True)
        time.sleep(pause_ms / 1000.0)

    success = last_status is not None and 200 <= last_status <= 399
    print(f"result {'success' if success else 'failure'} attempts {attempts_done}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())