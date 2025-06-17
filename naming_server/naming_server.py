import os
import uuid
import random
from flask import Flask, request, jsonify, abort
import requests
from requests.exceptions import RequestException, Timeout

app = Flask(__name__)

# list of storage server URLs from env
STORAGE_SERVERS = os.environ.get("STORAGE_SERVERS", "").split(",")
STORAGE_SERVERS = [s.strip() for s in STORAGE_SERVERS if s.strip()]
REPLICA_COUNT = int(os.environ.get("REPLICA_COUNT", "2"))
TIMEOUT = (3.05, 10)

files = {}  # filename -> {"chunks": [{"id": id, "servers": [url, ...]}], "size": int}

@app.route('/files/<name>', methods=['POST'])
def create_file(name):
    if not STORAGE_SERVERS:
        return jsonify({'error': 'No storage servers configured'}), 500
    content = request.data.decode('utf-8')
    chunks = [content[i:i+1024] for i in range(0, len(content), 1024)]
    entries = []
    for chunk in chunks:
        chunk_id = str(uuid.uuid4())
        servers = random.sample(
            STORAGE_SERVERS,
            min(REPLICA_COUNT, len(STORAGE_SERVERS))
        )
        stored = []
        for server in servers:
            url = f"{server}/chunks/{chunk_id}"
            try:
                resp = requests.post(
                    url,
                    data=chunk.encode('utf-8'),
                    timeout=TIMEOUT,
                )
                if resp.status_code == 200:
                    stored.append(server)
                else:
                    print(
                        f"Failed to store chunk {chunk_id} on {server}: "
                        f"{resp.status_code}"
                    )
            except Timeout:
                print("request timed out")
            except RequestException as e:
                print(f"Failed to store chunk {chunk_id} on {server}: {e}")
        if len(stored) < REPLICA_COUNT:
            for server in stored:
                try:
                    requests.delete(
                        f"{server}/chunks/{chunk_id}", timeout=TIMEOUT
                    )
                except Timeout:
                    print("request timed out")
                except RequestException:
                    pass
            return (
                jsonify({"error": "Insufficient storage for chunk", "chunk": chunk_id}),
                507,
            )
        entries.append({"id": chunk_id, "servers": stored})
    files[name] = {'chunks': entries, 'size': len(content)}
    return jsonify({'status': 'ok', 'chunks': entries})

@app.route('/files/<name>', methods=['GET'])
def read_file(name):
    meta = files.get(name)
    if not meta:
        abort(404)
    data = []
    for entry in meta['chunks']:
        chunk_data = None
        for server in entry['servers']:
            url = f"{server}/chunks/{entry['id']}"
            try:
                resp = requests.get(url, timeout=TIMEOUT)
                if resp.status_code == 200:
                    chunk_data = resp.text
                    break
            except Timeout:
                print("request timed out")
                continue
            except RequestException:
                continue
        if chunk_data is None:
            abort(500)
        data.append(chunk_data)
    return ''.join(data)

@app.route('/files/<name>', methods=['DELETE'])
def delete_file(name):
    meta = files.pop(name, None)
    if not meta:
        abort(404)
    for entry in meta['chunks']:
        for server in entry['servers']:
            url = f"{server}/chunks/{entry['id']}"
            try:
                requests.delete(url, timeout=TIMEOUT)
            except Timeout:
                print("request timed out")
            except RequestException as e:
                print(f"Failed to delete chunk {entry['id']} on {server}: {e}")
    return jsonify({'status': 'deleted'})

@app.route('/files/<name>/size', methods=['GET'])
def size_file(name):
    meta = files.get(name)
    if not meta:
        abort(404)
    return jsonify({'size': meta['size']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))

    from werkzeug.serving import make_server
    import signal

    server = make_server('0.0.0.0', port, app)

    def _shutdown(signum, frame):
        print(f'Received signal {signum}, shutting down...')
        server.shutdown()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    server.serve_forever()
