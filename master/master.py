import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Set
import random
from typing import TypedDict
import time

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import httpx

# GFS Master Node Implementation
class ChunkEntry(TypedDict):
    chunkserver_id: str
    chunk_id: int
    is_deleted: bool
    deleted_at: float | None

class Master:


    def __init__(self):
        self.rand = random.Random(69)
        self.replication_factor: int = 3 # Number of replicas for each chunk
        self.chunkserver_capacity: int = 5000 # The maximum number of characters a chunkserver can store
        self.max_chunk_size: int = 1000 # The number of characters in a chunk

        self.last_garbage_collection: float = 0.0  # Timestamp of the last garbage collection
        self.garbage_collection_time: float = 2 * 60  # Time in seconds before deleted chunks are eligible for garbage collection (default: 2 minutes)

        self.heartbeat_timeout: float = 5 * 60  # Time in seconds before a chunkserver is considered unresponsive

        self.chunkserver_ids: Set[str] = set()  # Set of registered chunkserver IDs
        self.last_heartbeat: Dict[str, float] = {}  # Stores last heartbeat time for each chunkserver
        self.chunkservers: Dict[str, Set[int]] = {}  # Maps chunkserver_id to set of stored chunks
        self.files: Dict[str, List[List[ChunkEntry]]] = {}  # Maps file path to list of chunk replicas, each replica is a dict with 'chunkserver_id' and 'chunk_id'

    def file_exists(self, path: str) -> bool:
        """
        Check if the file at the given path exists (not deleted).
        """
        path = self.format_path(path)
        if path not in self.files:
            return False

        for replicas in self.files[path]:
            for chunk in replicas:
                if chunk['is_deleted']:
                    return False
        return True

    def get_first_chunk(self, chunkserver_id: str) -> int:
        for chunk_id in range(self.chunkserver_capacity):
            if chunk_id not in self.chunkservers[chunkserver_id]:
                return chunk_id
        raise Exception("No available chunk found on the chunkserver.")   
    
    def get_random_chunkserver(self) -> str:
        if not self.chunkserver_ids:
            raise Exception("No chunkservers available.")
        
        chunkservers = list(self.chunkserver_ids)
        self.rand.shuffle(chunkservers)

        for chunkserver_id in chunkservers:
            if len(self.chunkservers[chunkserver_id]) < self.chunkserver_capacity:
                return chunkserver_id
            
        raise Exception("All chunkservers are at full capacity.")

    def allocate_chunk(self, chunkserver_id: str) -> ChunkEntry:
        try:
            chunk_id = self.get_first_chunk(chunkserver_id)
            self.chunkservers[chunkserver_id].add(chunk_id)
            chunk = ChunkEntry(
                chunkserver_id=chunkserver_id,
                chunk_id=chunk_id,
                is_deleted=False,
                deleted_at=None
            )
            return chunk
        except Exception as e:
            print(f"Error allocating chunk on server {chunkserver_id}: {e}")
            raise

    def allocate_chunks(self) -> List[ChunkEntry]:
        try:
            allocated_servers = []

            server_ids = list(self.chunkserver_ids)
            self.rand.shuffle(server_ids)

            for server_id in server_ids:
                if len(self.chunkservers[server_id]) < self.chunkserver_capacity:
                    allocated_servers.append(server_id)
                if len(allocated_servers) == self.replication_factor:
                    break            

            if len(allocated_servers) < self.replication_factor:
                raise Exception("Not enough chunkservers available to allocate chunks.")

            allocated_chunks = []
            for server_id in allocated_servers:
                try:
                    allocated_chunks.append(self.allocate_chunk(server_id))
                except Exception as e:
                    print(f"Error allocating chunk for server {server_id}: {e}")
                    continue

            if len(allocated_chunks) < self.replication_factor:
                raise Exception("Failed to allocate all required chunk replicas.")

            return allocated_chunks
        except Exception as e:
            print(f"Error occurred while allocating chunks: {e}")
            raise

    def format_path(self, path: str) -> str:
        if not path or not isinstance(path, str):
            raise ValueError("Invalid path provided.")
        
        return '/' + '/'.join(part for part in path.split('/') if part)

    def is_valid_path(self, path: str) -> bool:
        if not path or not isinstance(path, str):
            return False
        
        # Split path and check for empty segments (e.g., '//')
        parts = [p for p in path.split('/') if p]
        if not parts:
            return False

        # Check that none of the parent folders is a file
        current = ''
        for part in parts[:-1]:
            current += '/' + part
            if current in self.files:
                return False
            
        # Check that path is not a folder
        for path in self.files.keys():
            if path.startswith(self.format_path(path)) and path != self.format_path(path):
                return False

        return True

    def create_file(self, path: str, size: int) -> list[list[ChunkEntry]]:

        path = self.format_path(path)

        if self.file_exists(path):
            raise ValueError("File already exists at the specified path.")

        if not self.is_valid_path(path):
            raise ValueError("Invalid file path provided.")

        if size <= 0:
            raise ValueError("File size must be greater than zero.")
        
        chunk_count = (size + self.max_chunk_size - 1) // self.max_chunk_size

        allocated_chunks = []

        for i in range(chunk_count):
            try:
                chunks = self.allocate_chunks()
                allocated_chunks.append(chunks)
            except Exception as e:
                print(f"Error occurred while allocating chunks for file {path}: {e}")
                continue

        if len(allocated_chunks) < chunk_count:
            raise Exception("Failed to allocate all required chunks.")

        self.files[path] = allocated_chunks

        return allocated_chunks

    def get_file_chunks(self, path: str) -> List[List[ChunkEntry]]:
        if not self.is_valid_path(path):
            raise ValueError("Invalid file path provided.")

        path = self.format_path(path)

        
        
        if not self.file_exists(path):
            raise ValueError("File not found.")

        if path not in self.files:
            raise ValueError("File not found.")

        return self.files[path]

    def delete_file(self, path: str) -> bool:
        if not self.is_valid_path(path):
            raise ValueError("Invalid file path provided.")
        
        if not self.file_exists(path):
            raise ValueError("File does not exist or has already been deleted.")

        path = self.format_path(path)

        if path not in self.files:
            raise ValueError("File not found.")

        for replicas in self.files[path]:
            for chunk in replicas:
                chunk['is_deleted'] = True
                chunk['deleted_at'] = time.time()

        return True

    def register_chunkserver(self, chunkserver_id: str):
        if not chunkserver_id:
            raise ValueError("Invalid chunkserver ID provided.")

        self.chunkserver_ids.add(chunkserver_id)
        self.chunkservers[chunkserver_id] = set() 
        self.last_heartbeat[chunkserver_id] = time.time()

    def heartbeat(self, chunkserver_id: str) -> bool:
        if chunkserver_id not in self.chunkserver_ids:
            self.register_chunkserver(chunkserver_id)

        self.last_heartbeat[chunkserver_id] = time.time()
        return True
    
    def garbage_collection(self):
        current_time = time.time()
        if (current_time - self.last_garbage_collection) < self.garbage_collection_time:
            return
        
        for chunkserver_id in list(self.chunkserver_ids):
            chunk_ids = list(self.chunkservers[chunkserver_id])
            for chunk_id in chunk_ids:
                path, part_index = self.get_chunkentry_location(ChunkEntry(chunkserver_id=chunkserver_id, chunk_id=chunk_id))
                if path is None or part_index is None:
                    self.chunkservers[chunkserver_id].remove(chunk_id)

        for path, part in self.files.items():
            for replicas in part:
                for chunk in replicas:
                    if chunk['is_deleted'] and (current_time - chunk['deleted_at']) >= self.garbage_collection_time:
                        self.chunkservers[chunk['chunkserver_id']].remove(chunk['chunk_id'])
                        replicas.remove(chunk)

        self.last_garbage_collection = current_time

    def get_chunkentry_location(self, chunk: ChunkEntry):
        """
        Returns (file_path, part_index) for the given chunk entry.
        """
        for path, parts in self.files.items():
            for idx, replicas in enumerate(parts):
                for target_chunk in replicas:
                    if (target_chunk['chunkserver_id'] == chunk['chunkserver_id'] and
                        target_chunk['chunk_id'] == chunk['chunk_id']):
                        return path, idx
        return None, None

    async def replicate_chunk(self, chunk: ChunkEntry) -> ChunkEntry:

        path, part_index = self.get_chunkentry_location(chunk)

        replicas = self.files.get(path, []).copy()
        replicas.remove(chunk)

        if not replicas:
            raise ValueError("No replicas found for the specified chunk.")
        
        source_chunk = replicas[0]
        source_chunkserver_id = source_chunk['chunkserver_id']
        source_chunk_id = source_chunk['chunk_id']

        target_chunkserver_id = self.get_random_chunkserver()
        target_chunk_id = self.get_first_chunk(target_chunkserver_id)

        # Call the chunkserver to replicate the chunk data
        source_url = f"{source_chunkserver_id}/read_chunk/{source_chunk_id}"
        target_url = f"{target_chunkserver_id}/replicate_chunk"
        try:
            async with httpx.AsyncClient() as client:
                # Fetch chunk data from source chunkserver
                resp = await client.get(source_url)
                if resp.status_code != 200 or resp.json().get("status") != "success":
                    raise Exception("Failed to fetch chunk from source chunkserver")
                data = resp.json()["data"]
                # Send chunk data to target chunkserver
                payload = {
                    "source_chunkserver_id": source_chunkserver_id,
                    "source_chunk_id": source_chunk_id,
                    "target_chunk_id": target_chunk_id,
                    "data": data
                }
                resp2 = await client.post(target_url, json=payload)
                if resp2.status_code != 200 or resp2.json().get("status") != "success":
                    raise Exception("Failed to replicate chunk to target chunkserver")
        except Exception as e:
            print(f"Replication failed: {e}")
            raise

        # Create a new chunk entry for the target chunkserver only if replication succeeded
        new_chunk = ChunkEntry(
            chunkserver_id=target_chunkserver_id,
            chunk_id=target_chunk_id,
            is_deleted=False,
            deleted_at=None
        )

        self.chunkservers[target_chunkserver_id].add(target_chunk_id)
        self.files[path][part_index].append(new_chunk)

        return new_chunk

    def remove_chunkentry(self, chunk: ChunkEntry):
        path, part_index = self.get_chunkentry_location(chunk)

        self.files[path][part_index].remove(chunk)


    def replicate_chunkserver(self, chunkserver_id: str):
        
        if chunkserver_id not in self.chunkserver_ids:
            raise ValueError("Chunkserver not registered.")


        for path, parts in self.files.items():
            for replicas in parts:
                for chunk in replicas:
                    if chunk['chunkserver_id'] == chunkserver_id and not chunk['is_deleted']:
                        try:
                            new_chunk = asyncio.run(self.replicate_chunk(chunk))
                            print(f"Replicated chunk {chunk['chunk_id']} from {chunkserver_id} to {new_chunk['chunkserver_id']}")
                        except Exception as e:
                            print(f"Failed to replicate chunk {chunk['chunk_id']} from {chunkserver_id}: {e}")


    def disconnect_chunkserver(self, chunkserver_id: str, replicate: bool = True):
        if chunkserver_id not in self.chunkserver_ids:
            raise ValueError("Chunkserver not registered.")
        
        if replicate:
            self.replicate_chunkserver(chunkserver_id)

        self.chunkserver_ids.remove(chunkserver_id)
        del self.chunkservers[chunkserver_id]
        del self.last_heartbeat[chunkserver_id]

    def heartbeat_check(self):
        current_time = time.time()
        for chunkserver_id in list(self.chunkserver_ids):
            if chunkserver_id not in self.last_heartbeat or (current_time - self.last_heartbeat[chunkserver_id]) > self.heartbeat_timeout:
                print(f"Chunkserver {chunkserver_id} is unresponsive. Disconnecting...")
                self.disconnect_chunkserver(chunkserver_id)

master = Master()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------
# Request Models
# -------------------

class CreateFileRequest(BaseModel):
    path: str
    size: int

class DeleteFileRequest(BaseModel):
    path: str

class GetFileChunksRequest(BaseModel):
    path: str

class RegisterChunkserverRequest(BaseModel):
    chunkserver_id: str

class HeartbeatRequest(BaseModel):
    chunkserver_id: str

# -------------------
# API Endpoints
# -------------------

# -------- From Client --------
@app.post("/create_file")
def create_file(req: CreateFileRequest):
    try:
        return master.create_file(req.path, req.size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/delete_file")
def delete_file(req: DeleteFileRequest):
    try:
        return master.delete_file(req.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_file_chunks")
def get_file_chunks(path: str):
    try:
        return master.get_file_chunks(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# -------- From Chunkserver --------

@app.post("/register_chunkserver")
def register_chunkserver(req: RegisterChunkserverRequest):
    master.register_chunkserver(req.chunkserver_id)

@app.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    master.heartbeat(req.chunkserver_id)


# -------- Testing --------
@app.get("/test/get_chunkservers")
def get_chunkservers():
    return list(master.chunkserver_ids)

@app.get("/test/get_files")
def get_files():
    return list(master.files.keys())

@app.get("/test/get_chunkserver_chunks")
def get_chunkserver_chunks(chunkserver_id: str):
    return list(master.chunkservers.get(chunkserver_id, []))


async def serial_background_loop():
    while True:
        master.heartbeat_check()
        master.garbage_collection()
        await asyncio.sleep(5)

async def start_app():
    asyncio.create_task(serial_background_loop())
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_app())