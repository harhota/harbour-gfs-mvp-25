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
    def __init__(self, master_url: str = "http://localhost:8000"):
        self.host = "0.0.0.0"
        self.port = self.find_free_port()
        self.address = f"http://{self.get_ip_address()}:{self.port}"
        self.id = self.address
        self.master_url = master_url
        self.stored_chunks = set()
        self.heartbeat_interval = 10  # seconds

        self.app = FastAPI()

        # ✅ Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # or specify allowed origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.post("/write_chunk")
        async def write_chunk(chunk: ChunkPayload):
            # Ensure the directory for this chunkserver exists
            dir_path = os.path.join("chunks", self.id.replace(":", "_").replace("/", "_"))
            os.makedirs(dir_path, exist_ok=True)

            # Write the chunk data to a file named by chunk_id
            file_path = os.path.join(dir_path, f"{chunk.chunk_id}.chunk")
            with open(file_path, "w") as f:
                f.write(chunk.data)

            self.stored_chunks.add(chunk.chunk_id)
            return {"status": "success", "address": self.address}

        @self.app.get("/read_chunk/{chunk_id}")
        async def read_chunk(chunk_id: int):
            # Check if the chunk is stored
            if chunk_id not in self.stored_chunks:
                return {"status": "error", "message": "Chunk not found"}

            # Read the chunk data from the file
            dir_path = os.path.join("chunks", self.id.replace(":", "_").replace("/", "_"))
            file_path = os.path.join(dir_path, f"{chunk_id}.chunk")
            with open(file_path, "r") as f:
                data = f.read()

            return {"status": "success", "data": data}

    def find_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()

    async def register_with_master(self):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.master_url}/register_chunkserver",
                json={"chunkserver_id": self.address}
            )

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
