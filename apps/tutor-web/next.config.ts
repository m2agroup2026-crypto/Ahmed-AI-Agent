import type { NextConfig } from "next";
import path from "node:path";

const config: NextConfig = {
  turbopack: { root: path.resolve(__dirname, "../..") },
  // Explicit private development hosts only; never allow arbitrary origins.
  allowedDevOrigins: (process.env.AQLITH_DEV_HOSTS ?? "").split(",").map(host => host.trim()).filter(Boolean),
};

export default config;
