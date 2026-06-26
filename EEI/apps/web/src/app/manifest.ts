import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "商域图谱 / Enterprise Ecosystem Intelligence",
    short_name: "EEI",
    description: "企业商业版图与供应链递归探索系统",
    start_url: "/",
    display: "standalone",
    background_color: "#f6f7f9",
    theme_color: "#18201d",
    icons: [
      {
        src: "/eei-app-icon.png",
        sizes: "1254x1254",
        type: "image/png",
        purpose: "any"
      },
      {
        src: "/eei-app-icon.png",
        sizes: "1254x1254",
        type: "image/png",
        purpose: "maskable"
      }
    ]
  };
}
