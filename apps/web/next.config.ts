import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Monorepo: pin tracing root so a parent package-lock.json cannot confuse Next.
  outputFileTracingRoot: path.join(appDir, "../.."),
  transpilePackages: ["@wingsaver/openapi"],
};

export default nextConfig;
