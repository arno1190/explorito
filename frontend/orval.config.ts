import { defineConfig } from "orval";

export default defineConfig({
  explorito: {
    input: {
      target: "http://localhost:8005/openapi.json",
    },
    output: {
      mode: "tags-split",
      target: "src/lib/api/generated",
      schemas: "src/lib/api/model",
      client: "react-query",
      httpClient: "axios",
      override: {
        mutator: {
          path: "src/lib/api/axios-instance.ts",
          name: "axiosInstance",
        },
        query: {
          useQuery: true,
          useMutation: true,
          signal: true,
        },
      },
    },
    hooks: {
      afterAllFilesWrite: "pnpm exec prettier --write",
    },
  },
});
