/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
    domains: [
      "via.placeholder.com",
      "m.media-amazon.com",
      "i5.walmartimages.com",
      "images-na.ssl-images-amazon.com",
    ],
  },
};

export default nextConfig;
