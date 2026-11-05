# Onesa Drone mobile prototype — CHUBORY A77

This mobile application lives at `onesa-drone/frontend/mobile` and supports **iOS (including iPad)** and **Android** using Expo/React Native. It is a **simulation-only mission-planning and inspection-notes application**. The existing customer/admin React/Three.js drone console is preserved under `frontend/web/`; its original `frontend/` entrypoints remain temporarily for backward-compatible production packaging. The old deployment is unchanged by this PR.

## Hardware and current aircraft app

The prototype is the **CHUBORY A77 brushless drone**. The currently supplied app is [CHUBORY FLY](https://apps.apple.com/app/id6467178101). The CHUBORY A77 user documentation describes joining the aircraft Wi-Fi and viewing its camera / local controls in that app. A local Wi-Fi preview or app pairing does **not** establish an internet-accessible telemetry feed, public mobile SDK, GPS coordinates, flight-plan upload, autonomous patrol, encryption, remote video relay or command authorization.

Onesa does **not** connect to the real A77. No MAVLink, BLE, RC, serial, Wi-Fi command, camera or radio-control adapter is implemented. `physicalFlightCommandsEnabled` and `realA77TelemetryConnected` are permanently `false` in the current prototype. Onesa is not an alternative flight-control app.

## Mobile scope

- Mission types: **security rounds**, **farm irrigation/crop inspections**, **conservancy observation patrols**, **hospital supply delivery planning** and **e-commerce delivery planning**.
- Add latitude/longitude checkpoints, choose altitude for **simulation only**, view straight-line distance and inspect validation warnings. Generate a circular patrol or a bounded serpentine crop inspection route.
- Save/restore one mission draft and synthetic observation notes in the local protected device store. Explicitly export the route *for human review* using the device share sheet; exact coordinates are private.
- Advance a **simulated position** waypoint by waypoint. The Locate view always says **real position unavailable**. External map opening requires the user's tap and shares that point with the map provider.
- Dedicated video view shows **disconnected** until an independently commissioned lawful, authenticated, encrypted camera relay exists. CHUBORY FLY remains the appropriate original app for vendor-local video and manual control.
- Optional simulated inspection notes include observations and an explicitly simulated waypoint; no real-time video capture, cloud evidence chain or AI classification is claimed.

The simulation does not support autonomous launches, person tracking, individual identification, poacher recognition, pursuit, payload dropping or surveillance of individuals. Wildlife conservancy features should focus on safe, lawful area observations by authorized operators. A hospital route preview does not establish clinical chain-of-custody, transport safety, cold-chain handling, medical approval, or BVLOS permission.

## Local verification

```sh
cd onesa-drone
npm --prefix frontend/mobile ci
npm --prefix frontend/mobile run typecheck
npm --prefix frontend/mobile test
npm --prefix frontend/mobile run build
npm --prefix frontend/web ci
npm --prefix frontend/web run build
```

For physical iOS/Android development, run `npm --prefix frontend/mobile run native:generate` on the developer machine with Xcode or Android SDK. The generated `ios/` and `android/` platform files are intentionally not committed until device signing, runtime settings and native security have been reviewed. The folders include READMEs, not fully signed native apps. Real device acceptance is still required.

## Hardware and compliance gates before any flight integration

1. Confirm from the vendor the **exact A77 hardware/firmware**, whether GNSS exists, and whether a documented, licensed SDK or flight-plan protocol is offered. Do **not** reverse-engineer or inject into the local controller to bypass safeguards.
2. Use authorized pilot testing, local flight permission, visual line-of-sight and geographic/weather limitations. Review the rules of the relevant aviation authority: Zimbabwe **CAAZ**, and for any German testing, **LBA/EASA**. Cross-border/sensitive-facility operations require separate assessment.
3. Verify authenticated telemetry and video, encryption, key rotation and secure storage, consent/lawful privacy basis, fail-safe RTL/land, battery reserve, geo-awareness, operator veto and telemetry loss behavior on a test range before developing any physical command path.
4. Mission planning requires risk assessments for farms, people, livestock, wildlife, privacy and restricted airspace. Conservancy security footage must be protected and never imply guilt automatically.
5. Medical and e-commerce deliveries require validated payload mount/release, airworthiness/insurance, authorized destinations, delivery chain-of-custody, recipient verification and regulatory approval.
6. Keep simulation and real mission histories distinct; do not treat a simulated position or camera placeholder as observed hardware.
7. Integration into the existing Onesa Drone backend should use authorized identity roles and an explicit safe supervisor; the new mobile app currently stores drafts only and does **not** synchronize them to server fleet missions.

No hardware changes, production deployments, database migrations, or approval for physical flight are made by this feature branch.
