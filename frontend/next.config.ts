import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 反向代理到 FastAPI 后端（开发环境）
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/stream/:path*",
        destination: "http://localhost:8000/stream/:path*",
      },
      {
        source: "/confirm/:path*",
        destination: "http://localhost:8000/confirm/:path*",
      },
    ];
  },
};

export default nextConfig;
