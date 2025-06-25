/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_NAME_SERVER?: string
  readonly VITE_MASTER_URL?: string
  readonly VITE_CHUNKSERVER_1?: string
  readonly VITE_CHUNKSERVER_2?: string
  readonly VITE_CHUNKSERVER_3?: string
  // add more environment variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
