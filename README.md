# Distributed File System - GFS-inspired Implementation

## Overview

This project implements a distributed storage system inspired by **Google File System (GFS)**. The system is designed to handle large-scale data across many machines, providing fault tolerance, high throughput, and reliability by dividing files into chunks stored on multiple chunk servers coordinated by a master server.

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



# Technical Specifications

### Core Architecture
| Component          | Specification                          |
|--------------------|----------------------------------------|
| Replication Factor | 3 replicas per chunk (configurable)    |
| Chunk Size         | 1000 characters                        |
| Chunkserver Capacity | 5000 chunks per server               |
| Max File Size      | Limited by available chunkservers      |

### Performance Characteristics
| Metric             | Value                                  |
|--------------------|----------------------------------------|
| Heartbeat Interval | 10 seconds                             |
| Heartbeat Timeout  | 20 seconds                             |
| Garbage Collection | Runs every 2 minutes                   |
| Chunk Allocation   | Random distribution with capacity awareness |

### Fault Tolerance Features
- Automatic chunk replication
- Dead chunkserver detection via heartbeat
- Failed chunk re-replication
- Graceful chunkserver removal
- Deleted chunk retention (2 minutes before GC)

### Storage Management
| Feature            | Implementation                         |
|--------------------|----------------------------------------|
| Chunk Distribution | Random with capacity constraints       |
| Space Reclamation  | Time-delayed garbage collection        |
| Load Balancing     | Even distribution across chunkservers  |

### API Endpoints
**Master Server:**
- `/create_file` - Allocates chunks for new files
- `/delete_file` - Marks files for deletion
- `/get_file_chunks` - Returns chunk locations
- `/register_chunkserver` - Adds new storage nodes
- `/heartbeat` - Chunkserver health checks

**Chunk Server:**
- `/write_chunk` - Stores chunk data
- `/read_chunk` - Retrieves chunk data
- `/replicate_chunk` - Copies chunks between servers

Notes:

- The system uses a simplified version of the Google File System (GFS) concept.
- File data is split into chunks, replicated, and distributed across chunk servers.
- The frontend communicates with the master and chunk servers via API calls.

For any questions or issues, please refer to the project documentation or contact the maintainers.


