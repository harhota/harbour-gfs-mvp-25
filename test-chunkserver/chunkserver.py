import asyncio
import uuid
from fastapi import FastAPI, APIRouter
import httpx
import uvicorn


class ChunkServer:
    def __init__(self, master_url: str = "http://localhost:8000", port: int = 8001):
        self.id = str(uuid.uuid4())
        self.master_url = master_url
        self.port = port
        self.stored_chunks = set()
        
        # Create FastAPI app with our UUID as path prefix
        self.app = FastAPI()
        router = APIRouter(prefix=f"/{self.id}")
        
        @router.post("/write_chunk")
        async def write_chunk(chunk_id: int, data: str):
            self.stored_chunks.add(chunk_id)
            return {"status": "success", "chunkserver_id": self.id}
        
        @router.get("/read_chunk")
        async def read_chunk(chunk_id: int):
            if chunk_id in self.stored_chunks:
                return {"status": "success", "data": f"data for {chunk_id}", "chunkserver_id": self.id}
            return {"status": "error", "message": "Chunk not found"}
        
        @router.delete("/delete_chunk")
        async def delete_chunk(chunk_id: int):
            if chunk_id in self.stored_chunks:
                self.stored_chunks.remove(chunk_id)
                return {"status": "success", "chunkserver_id": self.id}
            return {"status": "error", "message": "Chunk not found"}
        
        self.app.include_router(router)

    async def register_with_master(self):
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.master_url}/register_chunkserver", json={"chunkserver_id": self.id})

    async def run(self):
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port)
        server = uvicorn.Server(config)
        
        await self.register_with_master()
        print(f"Chunkserver {self.id} running at http://localhost:{self.port}/{self.id}")
        await server.serve()

if __name__ == "__main__":
    chunkserver = ChunkServer()
    asyncio.run(chunkserver.run())