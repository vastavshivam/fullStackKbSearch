/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_HF_TOKEN: string
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
