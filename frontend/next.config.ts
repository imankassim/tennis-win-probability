import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal, self-contained server bundle
  // (.next/standalone) — infrastructure/Dockerfile.frontend copies just
  // that plus .next/static and public/, the pattern Next.js's own Docker
  // deployment docs recommend, rather than copying the full node_modules
  // tree into the runtime image.
  output: "standalone",
};

export default nextConfig;
