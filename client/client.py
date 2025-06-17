import sys
import os
import requests
from requests.exceptions import RequestException, Timeout

NAME_SERVER = os.environ.get('NAME_SERVER', 'http://localhost:8000')
TIMEOUT = (3.05, 10)

usage = """Usage:
  client.py create <filename> <local_path>
  client.py read <filename> <output_path>
  client.py delete <filename>
  client.py size <filename>
"""

def create(filename, local_path):
    with open(local_path, 'r', encoding='utf-8') as f:
        data = f.read()
    try:
        resp = requests.post(
            f"{NAME_SERVER}/files/{filename}",
            data=data.encode('utf-8'),
            timeout=TIMEOUT,
        )
        print(resp.text)
    except Timeout:
        print('request timed out')
    except RequestException as e:
        print(f'Error: {e}')

def read(filename, output_path):
    try:
        resp = requests.get(f"{NAME_SERVER}/files/{filename}", timeout=TIMEOUT)
        if resp.status_code == 200:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
        else:
            print('Error:', resp.text)
    except Timeout:
        print('request timed out')
    except RequestException as e:
        print(f'Error: {e}')

def delete(filename):
    try:
        resp = requests.delete(f"{NAME_SERVER}/files/{filename}", timeout=TIMEOUT)
        print(resp.text)
    except Timeout:
        print('request timed out')
    except RequestException as e:
        print(f'Error: {e}')

def size(filename):
    try:
        resp = requests.get(
            f"{NAME_SERVER}/files/{filename}/size", timeout=TIMEOUT
        )
        print(resp.text)
    except Timeout:
        print('request timed out')
    except RequestException as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'create' and len(sys.argv) == 4:
        create(sys.argv[2], sys.argv[3])
    elif cmd == 'read' and len(sys.argv) == 4:
        read(sys.argv[2], sys.argv[3])
    elif cmd == 'delete' and len(sys.argv) == 3:
        delete(sys.argv[2])
    elif cmd == 'size' and len(sys.argv) == 3:
        size(sys.argv[2])
    else:
        print(usage)
