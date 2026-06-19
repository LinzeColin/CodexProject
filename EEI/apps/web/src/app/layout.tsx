import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "商域图谱 | Enterprise Ecosystem Intelligence",
  description: "企业商业版图与供应链递归探索系统"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

