/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Linting is handled by Biome (npm run lint), not ESLint.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
