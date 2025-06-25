# Project README

## Overview

This project implements a distributed storage system inspired by **Google File System (GFS)**. GFS is designed to handle large-scale data across many machines, providing fault tolerance, high throughput, and reliability by dividing files into chunks stored on multiple chunk servers coordinated by a master server.

Our system includes:

- **Master Server:** Manages metadata, chunk locations, and client requests.
- **Chunk Servers:** Store file chunks and handle read/write operations.
- **Frontend (Client):** The user interface where users interact directly with the system to perform file operations. In this project, the client and frontend are combined.

## How It Works

- Files are split into fixed-size chunks.
- The Master Server maintains chunk metadata and their locations.
- Chunk Servers store chunks and replicate them to ensure fault tolerance.
- The Frontend communicates with backend servers to upload, download, and manage files.

## Running the Project with Docker Compose

1. Clone the repository:

   $ git clone <repository-url>
   $ cd <repository-folder>

2. Build and start all services (master server, chunk servers, frontend):

   $ docker-compose up --build

3. Open your browser and navigate to:

   http://localhost:5173/

4. Use the frontend interface to upload, download, and manage files within the distributed file system.

Architecture:

- Master Server: Maintains metadata for files and chunks, manages chunk locations and replication.
- Chunk Servers: Store chunks of files and handle client requests for data.
- Frontend (Client): Single combined client and frontend interface for users to interact with the system.

Notes:

- The system uses a simplified version of the Google File System (GFS) concept.
- File data is split into chunks, replicated, and distributed across chunk servers.
- The frontend communicates with the master and chunk servers via API calls.

For any questions or issues, please refer to the project documentation or contact the maintainers.
