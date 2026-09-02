import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone output keeps the production Docker image small (only the
  // traced dependency subset gets copied in, not the whole node_modules).
  output: "standalone",
};

export default nextConfig;
