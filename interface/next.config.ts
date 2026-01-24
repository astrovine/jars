import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  typescript: {
    // Allow production builds to complete even with type errors
    ignoreBuildErrors: true,
  },
  // @ts-ignore - ESLint config is valid but types may not recognize it
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
