import { AppProviders } from "./app/AppProviders";
import { FeatureRouter } from "./app/FeatureRouter";
import { MemoryAtlasShell } from "./app/MemoryAtlasShell";

export function App() {
  return (
    <AppProviders>
      <MemoryAtlasShell>
        <FeatureRouter />
      </MemoryAtlasShell>
    </AppProviders>
  );
}
