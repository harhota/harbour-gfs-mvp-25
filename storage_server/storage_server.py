import os
from flask import Flask, request, abort

app = Flask(__name__)

DATA_PATH = os.environ.get('DATA_PATH', 'data')
os.makedirs(DATA_PATH, exist_ok=True)

@app.route('/chunks/<chunk_id>', methods=['POST'])
def store_chunk(chunk_id):
    """Store a chunk on disk.

    Returns HTTP 507 if the storage volume is full.
    """
    path = os.path.join(DATA_PATH, chunk_id)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(request.data.decode('utf-8'))
    except OSError as e:
        if e.errno == 28:  # No space left on device
            return 'Insufficient storage', 507
        abort(500)
    return 'OK'

@app.route('/chunks/<chunk_id>', methods=['GET'])
def get_chunk(chunk_id):
    path = os.path.join(DATA_PATH, chunk_id)
    if not os.path.exists(path):
        abort(404)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/chunks/<chunk_id>', methods=['DELETE'])
def delete_chunk(chunk_id):
    path = os.path.join(DATA_PATH, chunk_id)
    if os.path.exists(path):
        os.remove(path)
    return 'DELETED'

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
