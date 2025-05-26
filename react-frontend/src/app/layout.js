import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "OpinionFlow - AI Product Review Intelligence",
  description:
    "AI-Powered Cross-Store Product Review Intelligence. Compare products across Amazon and Walmart with intelligent review analysis.",
  keywords:
    "product comparison, review analysis, AI, Amazon, Walmart, shopping intelligence",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
