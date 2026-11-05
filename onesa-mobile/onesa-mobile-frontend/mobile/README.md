# Onesa Mobile native preview

A compact React Native / Expo foundation for **iPhone, iPad and Android**. This is a development preview of the proposed Onesa Mobile customer experience in Zimbabwe. It is not a working mobile operator or a satellite connection application.

## What works

- Four native screens: Home, Plans, Network and Account.
- Local plan-concept selection, retained while switching tabs, and a reset action.
- Clear explanations of terrestrial mobile, direct phone-to-satellite service and Starlink broadband through Wi-Fi.
- A persistent development label, inactive service states and no invented coverage or network readings.
- Responsive compact layouts, system font scaling, safe-area handling, accessible button/tab labels and tablet-width limits.
- Branded app icons and splash screens, real generated Xcode and Android projects, and an iPad-capable iOS target (`TARGETED_DEVICE_FAMILY = "1,2"`).

Prices and allowances are deliberately unset until wholesale terms are known. Selecting a concept creates no order or subscription. All application data is local demonstration content; there is no application API connection, analytics, login, KYC collection, billing, payment collection, SIM provisioning or network control. Development tooling may connect to the local Metro server and Expo tooling; the privacy statements in the UI refer to application features.

The app neither detects satellite transport nor opts into constrained satellite data. A future satellite-compatible version will require device/carrier qualification, relevant Android declarations and Apple entitlements, and actual field testing. No such approval is implied here.

## Layout

| Path | Purpose |
| --- | --- |
| `App.tsx` | Native navigation and four preview screens |
| `src/ui.tsx` | Small visual components and the forest/mint theme |
| `src/domain.ts` | Local concepts, presentation state and blocked live actions |
| `src/domain.test.ts` | Preview isolation and reset checks |
| `app.json` | App identifiers, tablet support, permissions and generation configuration |
| `plugins/withPreviewSigning.cjs` | Reproducible Android signing configuration: per-developer debug key, unsigned release |
| `assets/` | Original geometric Onesa preview icons |
| `ios/` | Generated Xcode project and CocoaPods configuration |
| `android/` | Generated Android project and Gradle wrapper |

This package owns its dependencies and does not import components, runtime code or dependencies from the website or backend. An API contract can be introduced later without creating a shared runtime package.

## Run the preview

Use **Node.js 24 LTS** (at least 24.3, below 25) and npm. From this directory:

```sh
npm ci
npm start
```

Use an Expo Go version compatible with the pinned Expo SDK for a quick device preview, or use a local native development build. The lockfile pins the dependency graph. Expo SDK 58 compatibility is the baseline; a mismatched Expo Go version may require a development build.

### iPhone and iPad

On a Mac with a compatible Xcode, iOS Simulator and CocoaPods installation:

```sh
npm ci
npm run ios
```

Choose an iPhone or iPad simulator. Both use the same `ios/` project. Signing a physical-device build requires your own Apple developer configuration. No signing identity is included.

### Android

With Android Studio, the corresponding Android SDK/JDK and an emulator or authorised development device configured:

```sh
npm ci
npm run android
```

The Android toolchain uses the developer machine's standard debug signing configuration. Keystores are not committed. Release builds are intentionally unsigned; configure private release signing separately before distribution. The bundle/package identifiers end in `.preview` to keep this development app separate from any future customer app.

## Validate and regenerate

```sh
npm run typecheck
npm test
npm run export
```

`npm run verify` runs all three. The export command bundles the iOS and Android JavaScript with Metro and emits platform assets under ignored `dist/`. It does **not** compile an IPA, APK or AAB.

Native projects are checked in so that the repository has real platform projects. Treat `app.json` and `plugins/` as their configuration source; update them before regenerating:

```sh
npm run prebuild
```

Regeneration can rewrite native configuration. Review and preserve any intentional native changes before running it. The custom signing plugin fails explicitly if Expo changes the expected Gradle template, so signing behaviour must be reviewed during SDK upgrades.

## Verification status

Verified during foundation creation:

- TypeScript compilation without emitting files.
- Focused automated checks that plan choices do not enable live actions, reset clears preview state, and satellite service stays explicitly unavailable.
- Expo native project generation for both iOS and Android.
- Metro production JavaScript export for both platforms.
- Generated iOS project includes iPhone and iPad; generated Android permissions remove microphone, camera, location and legacy storage access.

**Not yet verified:** compilation with Xcode or the Android SDK, simulator or physical-device behaviour, VoiceOver/TalkBack, signed builds, store submission, real operator integration or satellite operation. Native binary builds and device checks are the next validation step before any distribution.

## Integration sequence

1. Confirm the regulatory model, licensed host and commercial scope.
2. Agree the authenticated API contract for Onesa identity, accounts, catalogues and readiness states.
3. Replace local concept data with the backend catalogue, including stale/offline states and bounded retry.
4. Add approved subscriber registration, account recovery and SIM/eSIM fulfilment using the host's supported workflows.
5. Add payment reconciliation, usage and invoices with server-side enforcement.
6. Qualify optional satellite capabilities independently for each market, plan, device and service.

The app must never infer live service from a user's selected plan or from an environment toggle. The current live-action boundary returns unavailable for every activation, payment and satellite action.

## Platform references

- [Expo project workflow](https://docs.expo.dev/workflow/overview/)
- [Expo config plugins](https://docs.expo.dev/config-plugins/plugins/)
- [Android app signing](https://developer.android.com/studio/publish/app-signing)
- [Android constrained satellite networks](https://developer.android.com/develop/connectivity/satellite/constrained-networks)

The generated platform build files originate from the official Expo SDK 58 bare template and React Native toolchain. Keep dependency licence notices and review them before distribution.
