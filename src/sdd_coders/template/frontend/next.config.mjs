/** @type {import('next').NextConfig} */

const isDev = process.env.NODE_ENV === "development";

// Content-Security-Policy for the frontend. Allows the third parties the
// template actually uses — Google Analytics (consent-gated) and Cloudflare
// Turnstile — and nothing else. Tighten per project as needed.
// Next.js dev mode (React Refresh / HMR) needs 'unsafe-eval', which is never
// added in production builds.
const scriptSrc = [
  "'self'",
  "'unsafe-inline'",
  isDev ? "'unsafe-eval'" : "",
  "https://www.googletagmanager.com",
  "https://challenges.cloudflare.com",
]
  .filter(Boolean)
  .join(" ");

// The frontend and the API live on different origins (e.g. example.com calling
// api.example.com), so the API base URL must be allowed in connect-src or every
// request is blocked by CSP.
const apiOrigin = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const connectSrc = [
  "'self'",
  apiOrigin,
  "https://www.google-analytics.com",
  "https://region1.google-analytics.com",
].join(" ");

const ContentSecurityPolicy = [
  "default-src 'self'",
  `script-src ${scriptSrc}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https://www.google-analytics.com",
  `connect-src ${connectSrc}`,
  "frame-src https://challenges.cloudflare.com",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: ContentSecurityPolicy },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(), microphone=(), camera=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
];

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Linting is handled by Biome (npm run lint), not ESLint.
  eslint: { ignoreDuringBuilds: true },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
