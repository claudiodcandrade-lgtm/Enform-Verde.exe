# V87.81 - Python/Windows module output parity - Enform Verde 3.26.11-PRECAMPO-EXPERIMENTAL
## Executable test requirements
- Source Python desktop_app.module_check runs the same offline diagnostic data as compiled Windows Enform Verde.exe --module-check.
- Compare exact values for application version, PronaSolos soil 0-100 cm synthetic *test fixture only*, pre-field evidence gate, IBGE microregion, PAM year count, panel yield model, SAR model manifest and SHA256, and simulated water balance coefficient Kc for soybean. This is an engineering fixture, NOT proof of real soil stocks or current agricultural yields.
- A missing field, failed SAR joblib hash or unequal output blocks Windows release. Include SAR model joblib and manifest files in PyInstaller; ensure dataroot under sys._MEIPASS.
- Independently verify executable launch and visual UI, actual optical CBERS-4A or Sentinel-2 pixel access, real Sentinel-1 RTC VV/VH pixel access, and Tapajos geospatial acceptance from a clean copied application folder. Preserve full diagnostics and fail on mismatches.
- Regression suites and release build must use exactly the same source SHA; previous jobs passed on a historical commit are not evidence for later commits.
- This test covers deterministic core modules; it does not yet establish full Python/Windows equivalence across all native-carbon, optical and agricultural workflows for every AOI and biome. Full Fazenda Maria Eduarda KML and observational field validation are pending.
