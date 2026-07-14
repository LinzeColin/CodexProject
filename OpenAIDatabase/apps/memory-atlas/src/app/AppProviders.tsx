import type { PropsWithChildren } from "react";
import { AtlasDataProvider } from "../providers/AtlasDataProvider";
import { AtlasRuntimeProvider } from "../providers/AtlasRuntimeProvider";
import { AtlasWorkspaceProvider } from "../providers/AtlasWorkspaceProvider";

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <AtlasDataProvider>
      <AtlasWorkspaceProvider>
        <AtlasRuntimeProvider>{children}</AtlasRuntimeProvider>
      </AtlasWorkspaceProvider>
    </AtlasDataProvider>
  );
}
