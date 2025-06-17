# Harbour Distributed File System (MVP)

This project is a minimal distributed file system designed for text files. It
consists of a single **naming server**, multiple **storage servers** and a
simple **CLI client**.

## Architecture

```
+------------+       +---------------+
|  Client    +<----->+ Naming Server |
+------------+       +---------------+
                          |  |
              +-----------+  +-----------+
              |                         |
       +-------------+           +-------------+
       | Storage #1  |   ...     | Storage #N  |
       +-------------+           +-------------+
```

- **Naming server** keeps file metadata and knows where every file chunk is
  stored.
- **Storage servers** store 1&nbsp;KB chunks of files. Each chunk is replicated on
  multiple storage servers.
- **Client** provides commands to create, read, delete and get the size of a
  file.

## Features

- Text file support only
- Fixed chunk size: **1&nbsp;KB**
- Operations: `create`, `read`, `delete`, `size`
- Chunk replication (replica count configurable via environment)
- Dockerized naming and storage servers
- Graceful error when storage volumes run out of space
- Client and naming server requests use a timeout by default to avoid hangs

## Running with Docker

This repository contains a `docker-compose.yml` that launches one naming server
and two storage servers. Docker images are built from the provided Dockerfiles.

```
docker-compose up --build
```

The naming server will listen on port **8000**, while the two storage servers
will listen on ports **8001** and **8002**. The naming server automatically
connects to both storage servers via the `STORAGE_SERVERS` environment variable
set in `docker-compose.yml`.

## Using the Client

The client communicates with the naming server using HTTP. After the services are
running you can use the client to interact with the distributed file system.

```
# Create a file
python client/client.py create myfile.txt ./local.txt

# Read the file back
python client/client.py read myfile.txt ./output.txt

# Get size information
python client/client.py size myfile.txt

# Delete the file
python client/client.py delete myfile.txt
```

Set the `NAME_SERVER` environment variable if the naming server is not running on
`http://localhost:8000`.

```
export NAME_SERVER=http://<naming-host>:8000
```

## Development Notes

- `requirements.txt` lists the Python dependencies (`flask` and `requests`).
- The naming server distributes chunks to storage servers at upload time and
  keeps all metadata in memory (non‑persistent demo implementation).
- Storage servers write chunk files under their `/data` directory. If a storage
  volume is full the server returns HTTP 507 so uploads fail fast.

This MVP aims to demonstrate the basic idea of a distributed file system with
chunking and replication. It is **not** intended for production use but serves as
a starting point for experimentation.
