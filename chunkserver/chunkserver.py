import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
import asyncio
import os

class ChunkPayload(BaseModel):
    chunk_id: int
    data: str

class ChunkServer:
    def __init__(self, master_url: str = "http://master:8000"):
        self.host = "0.0.0.0"
        self.port = 8000
        chunkserver_id = os.getenv("CHUNKSERVER_ID", socket.gethostname())
        self.id = chunkserver_id
        self.address = f"http://{self.id}:{self.port}"

        self.master_url = master_url
        self.stored_chunks = set()
        self.heartbeat_interval = 10  # seconds

        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.post("/write_chunk")
        async def write_chunk(chunk: ChunkPayload):
            dir_path = os.path.join("chunks", self.id.replace(":", "_").replace("/", "_"))
            os.makedirs(dir_path, exist_ok=True)

            file_path = os.path.join(dir_path, f"{chunk.chunk_id}.chunk")
            with open(file_path, "w") as f:
                f.write(chunk.data)

            self.stored_chunks.add(chunk.chunk_id)
            return {"status": "success", "address": self.address}

        @self.app.get("/read_chunk/{chunk_id}")
        async def read_chunk(chunk_id: int):
            if chunk_id not in self.stored_chunks:
                return {"status": "error", "message": "Chunk not found"}

            dir_path = os.path.join("chunks", self.id.replace(":", "_").replace("/", "_"))
            file_path = os.path.join(dir_path, f"{chunk_id}.chunk")
            with open(file_path, "r") as f:
                data = f.read()

            return {"status": "success", "data": data}

        @self.app.post("/replicate_chunk")
        async def replicate_chunk(source_chunkserver_id: str, source_chunk_id: int, target_chunk_id: int):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{source_chunkserver_id}/read_chunk/{source_chunk_id}")
                    if resp.status_code != 200 or resp.json().get("status") != "success":
                        return {"status": "error", "message": "Failed to fetch chunk from source"}
                    data = resp.json()["data"]
            except Exception as e:
                return {"status": "error", "message": f"Error contacting source chunkserver: {e}"}

            dir_path = os.path.join("chunks", self.id.replace(":", "_").replace("/", "_"))
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, f"{target_chunk_id}.chunk")
            with open(file_path, "w") as f:
                f.write(data)

            self.stored_chunks.add(target_chunk_id)
            return {"status": "success", "message": f"Chunk {source_chunk_id} replicated as {target_chunk_id}"}

    def find_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    async def register_with_master(self):
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    resp = await client.post(
                        f"{self.master_url}/register_chunkserver",
                        json={"chunkserver_id": self.address}
                    )
                    if resp.status_code == 200:
                        print(f"✅ Registered with master at {self.master_url}")
                        break
                    else:
                        print(f"⚠️ Failed to register with master, status: {resp.status_code}")
                except Exception as e:
                    print(f"⚠️ Could not connect to master ({self.master_url}), retrying in 2 seconds... ({e})")
                await asyncio.sleep(2)

    async def send_heartbeat_loop(self):
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    await client.post(
                        f"{self.master_url}/heartbeat",
                        json={"chunkserver_id": self.address}
                    )
                except Exception as e:
                    print(f"❌ Heartbeat failed: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def run(self):
        await self.register_with_master()
        asyncio.create_task(self.send_heartbeat_loop())

        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        print(f"✅ Chunkserver running at {self.address}")
        await server.serve()

if __name__ == "__main__":
    server = ChunkServer()
    asyncio.run(server.run())
