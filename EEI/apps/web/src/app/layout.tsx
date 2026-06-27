import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  applicationName: "EEI 商域图谱",
  title: "商域图谱 | Enterprise Ecosystem Intelligence",
  description: "企业商业版图与供应链递归探索系统",
  icons: {
    icon: [
      { url: "/eei-app-icon.svg", type: "image/svg+xml" },
      { url: "/eei-app-icon.png", sizes: "1024x1024", type: "image/png" }
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }]
  },
  appleWebApp: {
    title: "EEI 商域图谱",
    capable: true,
    statusBarStyle: "black-translucent"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
