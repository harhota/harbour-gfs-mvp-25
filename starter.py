#!/usr/bin/env python3
import asyncio
import subprocess
import os
import signal
import sys
from typing import List

class GFSCluster:
    def __init__(self):
        self.master_process = None
        self.chunkserver_tasks: List[asyncio.Task] = []
        self.master_port = 8000
        self.chunkserver_port = 8001  # All chunkservers use same port
        self.num_chunkservers = 5

    async def start_master(self):
        """Start the master server"""
        print("🚀 Starting GFS Master Server...")
        self.master_process = subprocess.Popen(
            ["uvicorn", "master:app", "--host", "0.0.0.0", "--port", str(self.master_port), "--app-dir", "./master"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        await asyncio.sleep(2)  # Wait for master to start
        print(f"✅ Master running at http://localhost:{self.master_port}")

    async def start_chunkserver(self, server_id: int):
        """Start a single chunkserver instance"""
        proc = subprocess.Popen(
            ["python", "test-chunkserver/chunkserver.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            env={**os.environ, "CHUNKSERVER_PORT": str(self.chunkserver_port)}
        )
        print(f"  Chunkserver {server_id} starting...")
        return proc

    async def run(self):
        """Run the entire cluster"""
        try:
            await self.start_master()
            
            # Start chunkservers
            print(f"\n🛠️  Starting {self.num_chunkservers} chunkservers on port {self.chunkserver_port}...")
            for i in range(self.num_chunkservers):
                await self.start_chunkserver(i+1)
                await asyncio.sleep(0.5)  # Stagger startup
            
            print("\n🌐 GFS Cluster is running!")
            print(f"All chunkservers accessible via port {self.chunkserver_port}/<uuid>")
            print("Press Ctrl+C to shutdown\n")
            
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of all processes"""
        print("\n🛑 Shutting down cluster...")
        if self.master_process:
            self.master_process.terminate()
        print("✅ Cluster shutdown complete")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("master", exist_ok=True)
    os.makedirs("test-chunkserver", exist_ok=True)
    
    # Run the cluster
    cluster = GFSCluster()
    loop = asyncio.get_event_loop()
    
    def signal_handler(sig, frame):
        cluster.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        loop.run_until_complete(cluster.run())
    finally:
        loop.close()