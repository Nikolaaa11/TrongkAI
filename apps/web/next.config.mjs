/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: { allowedOrigins: ['localhost:3000'] },
  },
  env: {
    ENGINE_URL: process.env.ENGINE_URL ?? 'http://localhost:8000',
  },
};

export default nextConfig;
