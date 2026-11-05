# Onesa Drone mobile field operations

iOS and Android React Native/Expo SDK 58 prototype. Production aircraft control is deliberately **disabled** by the Onesa Drone engineering policy.

## Implemented in the app

- Manual latitude/longitude waypoints with validation, distance review, interactive relative map, route editing and saved mission drafts.
- Security rounds, farm inspections, conservancy observation, medical-delivery and e-commerce-delivery planning templates.
- Local-only route simulation with positions explicitly identified as synthetic. Hardware position, battery and camera state remain unavailable without a verified source.
- Private per-draft platform-encrypted storage through Expo SecureStore, with tests for corrupted data and index failures.
- Camera panel explaining the local CHUBORY FLY Wi-Fi feed and offering an external handoff to the official companion app.
- Safety checklist and no remote flight, mission launch, take-off, payload release, human tracking, automated surveillance or live video endpoints.

## Setup and tests

```bash
cd onesa-drone/frontend/drone/mobile
npm install
npm test
npx expo install --check
npm run export
npm run ios       # Mac + Xcode
npm run android   # Android SDK
```

`ios/` and `android/` contain the platform build targets; Expo prebuild generates platform-specific Xcode/Gradle source there. The Expo runtime and host OS tools are required for compiled native acceptance. The GitHub-hosted Node tests exercise planning, simulation and secure-store business rules, not physical A77 hardware.

## Integration boundary

The CHUBORY A77 uses CHUBORY FLY (iOS App Store ID 6467178101; Android `com.h8.chubory`). The vendor advertises Wi-Fi control, video, and trajectory flight, **not** a documented third-party SDK or authenticated GPS/RTSP telemetry endpoint. Onesa never reverse-engineers unsafe flight commands or assumes a phone location is the drone location.

A later supported aircraft adapter must authenticate telemetry, prove source/freshness, restrict video URLs and audit every access; pass supervised flight test and operator/regulatory acceptance before any physical dispatch. Long-range wildlife patrols and medical deliveries require suitable aircraft and aviation approvals and are not supported by this prototype.

No map tiles are sent to third parties: route sketches use local SVG geometry and are not airspace maps. Do not use demo coordinates as actual airspace/terrain clearances.
