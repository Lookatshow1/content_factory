/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    // Внутри Docker используем имя сервиса 'backend'
    const apiUrl = 'http://backend:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/media/:path*',
        destination: `${apiUrl}/media/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
