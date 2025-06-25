#!/usr/bin/env python3
import asyncio
import subprocess
import time

async def start_services():
    print("🚀 Starting master server...")
    master = subprocess.Popen(
        ["uvicorn", "master:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="./master"
    )
    
    print("\n🛠️ Starting chunkservers...")
    chunkservers = []
    for i in range(5):
        chunkserver = subprocess.Popen(
            ["python3", "chunkserver.py"],
            cwd="./chunkserver"
        )

        chunkservers.append(chunkserver)
        time.sleep(0.5)  # Stagger startup
    
    return master, chunkservers

async def main():
    master, chunkservers = await start_services()
    print("\n🌐 Cluster running!")
    print("Master: http://localhost:8000")
    print("Chunkservers will auto-register their addresses")
    
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        master.terminate()
        for cs in chunkservers:
            cs.terminate()

if __name__ == "__main__":
    asyncio.run(main())