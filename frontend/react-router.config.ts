import type { Config } from "@react-router/dev/config"

export default {
  // SPA: build estático em build/client, servido pelo FastAPI
  ssr: false,
} satisfies Config
