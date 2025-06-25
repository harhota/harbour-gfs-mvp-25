import socket
from fastapi import FastAPI
import uvicorn
import httpx
import asyncio

class ChunkServer:
    def __init__(self, master_url: str = "http://localhost:8000"):
        self.host = "0.0.0.0"
        self.port = self.find_free_port()
        self.address = f"http://{socket.gethostname()}:{self.port}"
        self.master_url = master_url
        self.stored_chunks = set()
        self.heartbeat_interval = 10  # seconds
        
        self.app = FastAPI()
        
        @self.app.post("/write_chunk")
        async def write_chunk(chunk_id: int, data: str):
            self.stored_chunks.add(chunk_id)
            return {"status": "success", "address": self.address}
            
        @self.app.get("/read_chunk/{chunk_id}")
        async def read_chunk(chunk_id: int):
            if chunk_id in self.stored_chunks:
                return {"data": f"data from {self.address}"}
            return {"error": "Chunk not found"}

    def find_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 0))
            return s.getsockname()[1]

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

        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        print(f"✅ Chunkserver running at {self.address}")
        await server.serve()


if __name__ == "__main__":
    server = ChunkServer()
    asyncio.run(server.run())
