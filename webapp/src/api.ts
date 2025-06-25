const BASE_URL = import.meta.env.VITE_NAME_SERVER ?? 'http://localhost:8000'

export async function uploadFileRequest(filename: string, data: string): Promise<string> {
  // 1. Create file and get chunk allocation
  const res = await fetch(`${BASE_URL}/create_file`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: filename,
      size: data.length,
    }),
  })
  if (!res.ok) throw new Error(await res.text())

  // 2. Get the chunk allocation
  const chunksRes = await fetch(`${BASE_URL}/get_file_chunks?path=${encodeURIComponent(filename)}`)
  if (!chunksRes.ok) throw new Error(await chunksRes.text())
  const chunkSets: Array<
    Array<{
      chunkserver_id: string
      chunk_id: number
      is_deleted: boolean
      deleted_at: number | null
    }>
  > = await chunksRes.json()

  // 3. Split data into chunks (max 1000 chars each)
  const MAX_CHUNK_SIZE = 1000
  const totalChunks = chunkSets.length
  const chunks: string[] = []

  for (let i = 0; i < totalChunks; i++) {
    const start = i * MAX_CHUNK_SIZE
    const end = Math.min(start + MAX_CHUNK_SIZE, data.length)
    chunks.push(data.slice(start, end))
  }

  // 4. Write each chunk to all its replicas
  const writePromises = chunkSets.map(async (replicas, chunkIndex) => {
    const chunkData = chunks[chunkIndex]

    // Write to all replicas in parallel
    const replicaPromises = replicas.map(async (replica) => {
      const writeRes = await fetch(`${replica.chunkserver_id}/write_chunk/${replica.chunk_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: chunkData }),
      })
      if (!writeRes.ok) {
        throw new Error(`Failed to write to ${replica.chunkserver_id}: ${await writeRes.text()}`)
      }
      return writeRes.json()
    })

    await Promise.all(replicaPromises)
  })

  // 5. Wait for all chunks to be written
  await Promise.all(writePromises)
  return 'File uploaded successfully'
}

export async function readFileRequest(filename: string): Promise<string> {
  // 1. Get chunk metadata from master
  const res = await fetch(`${BASE_URL}/get_file_chunks?path=${encodeURIComponent(filename)}`)
  if (!res.ok) throw new Error(await res.text())
  const chunkSets: Array<
    Array<{
      chunkserver_id: string
      chunk_id: number
      is_deleted: boolean
      deleted_at: number | null
    }>
  > = await res.json()

  // 2. Helper function to resolve chunkserver URL
  const resolveChunkserverUrl = (chunkserver_id: string): string => {
    if (chunkserver_id.startsWith('http://') || chunkserver_id.startsWith('https://')) {
      return chunkserver_id
    }
    return `http://${chunkserver_id}`
  }

  // 3. Fetch data from each chunk in parallel
  const chunkPromises = chunkSets.map(async (replicas, index) => {
    // Try each replica until one succeeds
    for (const replica of replicas) {
      if (replica.is_deleted) continue

      try {
        const chunkserverUrl = resolveChunkserverUrl(replica.chunkserver_id)
        const chunkRes = await fetch(`${chunkserverUrl}/read_chunk/${replica.chunk_id}`)
        if (chunkRes.ok) {
          return await chunkRes.text()
        }
      } catch (error) {
        // Try next replica
        continue
      }
    }
    throw new Error(`Failed to read chunk ${index} from all replicas`)
  })

  // 4. Wait for all chunks and concatenate in order
  const chunkData = await Promise.all(chunkPromises)
  return chunkData.join('')
}

export async function deleteFileRequest(filename: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/delete_file`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: filename,
    }),
  })
  if (!res.ok) throw new Error(await res.text())
  return 'File deleted successfully'
}

export async function fileSizeRequest(filename: string): Promise<number> {
  const res = await fetch(`${BASE_URL}/get_file_chunks?path=${encodeURIComponent(filename)}`)
  if (!res.ok) throw new Error(await res.text())
  const chunks = await res.json()
  // Assuming each chunk is max 1000 characters (from master.py max_chunk_size)
  // TODO: should be real size, not max_chunk_size * chunks.length
  const validChunks = chunks.filter((replicas: any[]) => replicas.length > 0 && replicas.every((c: any) => !c.is_deleted))
  return validChunks[0].length * 1000
}
