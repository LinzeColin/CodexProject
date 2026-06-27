# EEI App Icon

The EEI icon uses three product signals:

- Enterprise monogram: a high-contrast `E` mark for Enterprise Ecosystem Intelligence.
- Recursive ecosystem map: connected nodes and rings represent company, supply-chain, capital and policy relationship traversal.
- Evidence-grade visual system: dark teal base, cyan data paths, amber decision signals and non-monochrome contrast for small macOS Dock sizes.

Generated files:

- `assets/app_icon/EEIAppIcon.svg`
- `assets/app_icon/EEIAppIcon.png`
- `assets/app_icon/EEIAppIcon.icns`
- `apps/web/public/eei-app-icon.svg`
- `apps/web/public/eei-app-icon.png`
- `apps/web/public/apple-touch-icon.png`

Regenerate and install locally:

```bash
python scripts/generate_app_icon.py --install-app /Applications/EEI.app --verify-app /Applications/EEI.app
```
