const BASE_URL = import.meta.env.VITE_NAME_SERVER ?? 'http://localhost:8000';

export async function uploadFileRequest(filename: string, data: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/files/${encodeURIComponent(filename)}`, {
    method: 'POST',
    body: data,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.text();
}

export async function readFileRequest(filename: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/files/${encodeURIComponent(filename)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.text();
}

export async function deleteFileRequest(filename: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.text();
}

export async function fileSizeRequest(filename: string): Promise<number> {
  const res = await fetch(`${BASE_URL}/files/${encodeURIComponent(filename)}/size`);
  if (!res.ok) throw new Error(await res.text());
  const data: { size: number } = await res.json();
  return data.size;
}
