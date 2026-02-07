# Swift Android Build Tools

Command-line tools for **building** and **testing** Swift packages on Android devices. Works with any SDK compatible with the [official Swift SDK for Android](https://www.swift.org/documentation/articles/swift-sdk-for-android-getting-started.html). Used at [Readdle](https://readdle.com) to build [Spark](https://sparkmailapp.com) for Android.

## Supported SDKs

These tools work with any Swift SDK for Android that follows the official artifact bundle layout:

- **[Official Swift SDK for Android](https://www.swift.org/documentation/articles/swift-sdk-for-android-getting-started.html)** - provided by the Swift Android Working Group of the Swift open source project, available for macOS and Linux.
- **[Readdle Swift Android Toolchain](https://github.com/readdle/swift-android-toolchain)** - a fork with Readdle-specific patches. Used as the **default** SDK path (see [Environment Variables](#environment-variables)).

Any other SDK that is compatible with the official one can be used by setting `SWIFT_ANDROID_SDK_HOME`.

## Overview

This toolkit provides two commands through a unified `swift-android` dispatcher:

| Command | Description |
|---|---|
| `swift-android build` | Cross-compile a Swift package for Android |
| `swift-android test` | Build, deploy, and run XCTest suites on a connected Android device |

Both tools wrap Swift Package Manager and use the configured SDK artifact bundle to produce native Android binaries. Test execution is handled over ADB.

## Prerequisites

- **Swift** toolchain (managed via [Swiftly](https://swiftlang.github.io/swiftly/), defaults to 6.2)
- **Swift SDK for Android** artifact bundle (see [Supported SDKs](#supported-sdks))
- **Android Debug Bridge (ADB)** on your `PATH` (from Android SDK Platform-Tools)
- **Python 3** (for the test runner)
- A connected Android device or emulator (for `swift-android test`)

## Installation

Clone the repository and add it to your `PATH`:

```bash
git clone https://github.com/nicklama/swift-android-buildtools.git
export PATH="$PATH:/path/to/swift-android-buildtools"
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SWIFT_ANDROID_SDK_HOME` | `~/Library/org.swift.swiftpm/swift-sdks/readdle-swift-6.2.1-RELEASE_android.artifactbundle` | Root of the Swift SDK for Android artifact bundle. The default points to the Readdle SDK on macOS. When using the official SDK or running on Linux, you **must** set this to your SDK installation path. |
| `SWIFT_ANDROID_ARCH` | `aarch64` | Target CPU architecture. See [Architecture Support](#architecture-support). |
| `SWIFT_ANDROID_API_LEVEL` | `29` | Minimum Android API level (Android 10 by default). |
| `ANDROID_SERIAL` | *(none)* | Default ADB device serial. Can be overridden per-invocation with `--device`. |
| `X_ANDROID_*` | *(none)* | Any environment variable prefixed with `X_ANDROID_` is forwarded to the Android device at test execution time with the prefix stripped. For example, `X_ANDROID_MY_VAR=1` becomes `MY_VAR=1` on the device. |

## Architecture Support

Three Android architectures are supported:

| `SWIFT_ANDROID_ARCH` | SDK Triple | NDK Triple | Android ABI | Notes |
|---|---|---|---|---|
| `aarch64` *(default)* | `aarch64-unknown-linux-android` | `aarch64-linux-android` | `arm64-v8a` | Most modern phones and tablets |
| `x86_64` | `x86_64-unknown-linux-android` | `x86_64-linux-android` | `x86_64` | Emulators, some Chromebooks |
| `armv7` | `armv7-unknown-linux-androideabi` | `arm-linux-androideabi` | `armeabi-v7a` | Legacy 32-bit ARM devices |
Set the architecture before building:

```bash
export SWIFT_ANDROID_ARCH=x86_64
swift-android build
```

---

## swift-android build

Cross-compiles a Swift package for Android using Swift Package Manager.

### Usage

```
swift-android build [options...]
```

All arguments are forwarded directly to `swift build`, so any flag accepted by Swift PM can be used.

### What It Does

1. Resolves the target architecture from `SWIFT_ANDROID_ARCH` (defaults to `aarch64`)
2. Resolves the API level from `SWIFT_ANDROID_API_LEVEL` (defaults to `29`)
3. Constructs the Swift SDK triple (e.g. `aarch64-unknown-linux-android29`)
4. Auto-detects the Swift version from the SDK's `sbom.spdx.json` (falls back to 6.2)
5. Invokes `swift build` via Swiftly with:
   - `--swift-sdk <triple>` to target Android
   - `-Xbuild-tools-swiftc -DTARGET_ANDROID` compile flag
   - `-Xbuild-tools-swiftc -D<TRIPLE_FLAG>` architecture-specific compile flag
6. Forwards all additional arguments to `swift build`

### Compiler Flags

The build tool automatically defines these compile-time flags for build tool plugins and package manifest conditions:

| Flag | When Defined |
|---|---|
| `TARGET_ANDROID` | Always (every Android build) |
| `TRIPPLE_AARCH64_LINUX_ANDROID` | `SWIFT_ANDROID_ARCH=aarch64` or unset |
| `TRIPPLE_X86_64_LINUX_ANDROID` | `SWIFT_ANDROID_ARCH=x86_64` |
| `TRIPPLE_ARM_LINUX_ANDROID` | `SWIFT_ANDROID_ARCH=armv7` |
These flags are passed via `-Xbuild-tools-swiftc` and are available in your `Package.swift` build tool plugin code.

### Examples

**Build for the default architecture (aarch64, API 29):**

```bash
swift-android build
```

**Build in release mode:**

```bash
swift-android build -c release
```

**Build for x86_64 emulator:**

```bash
SWIFT_ANDROID_ARCH=x86_64 swift-android build
```

**Build targeting a specific API level:**

```bash
SWIFT_ANDROID_API_LEVEL=24 swift-android build
```

**Build a specific product:**

```bash
swift-android build --product MyLibrary
```

**Build with verbose output:**

```bash
swift-android build -v
```

---

## swift-android test

Builds, deploys, and runs Swift XCTest suites on a connected Android device via ADB. This is a three-phase tool: **build**, **push**, and **execute**.

### Usage

```
swift-android test [options...] [-Xbuild <arg>] [-Xtest <arg>]
```

### Options

#### Device Selection

| Flag | Description |
|---|---|
| `-s`, `--serial`, `--device` `<serial>` | Use the Android device with the given serial number. Overrides the `ANDROID_SERIAL` environment variable. |

#### Shortcut Modes

| Flag | Description |
|---|---|
| `-f`, `--fast`, `--just-run` | **Fast mode.** Skip both building and pushing; only execute tests on the device. Equivalent to `--skip-build --skip-push`. |
| `-d`, `--deploy` | **Deploy mode.** Build and push to the device but do not run tests. Equivalent to `--skip-testing`. Useful for manual execution with profiling or debugging tools. |

#### Build Phase Control

| Flag | Description |
|---|---|
| `--skip-build` | Skip the build step. Only deploy and run. Useful when the binary is already compiled. |

#### Push Phase Control

| Flag | Description |
|---|---|
| `--skip-push` | Skip all file deployment. Only run tests with whatever is already on the device. |
| `--skip-push-stdlib` | Don't push Swift standard library and runtime `.so` files to the device. Saves time if the stdlib hasn't changed. |
| `--skip-push-external` | Don't push externally built dependency libraries (`.so` from artifact outputs). |

#### Execution Phase Control

| Flag | Description |
|---|---|
| `--skip-testing` | Don't execute tests on the device after building and deploying. Useful for deploying, then manually running with tools like `simpleperf`, `lldb`, etc. |

#### Argument Forwarding

| Flag | Description |
|---|---|
| `-Xbuild <arg>` | Forward an argument to Swift Package Manager during the build phase. Can be specified multiple times. Example: `-Xbuild -v` for verbose build output. |
| `-Xtest <arg>` | Forward an argument to the XCTest runner on the device. Can be specified multiple times. Example: `-Xtest --filter -Xtest MyTests.testFoo`. |

> **Note:** Thanks to a custom argument parser, you can write `-Xbuild -v` instead of the more verbose `-Xbuild='-v'` syntax.

### What It Does

The test runner executes up to three phases:

#### Phase 1: Build

Invokes `swift-android build --build-tests` (plus any `-Xbuild` arguments) to compile the test bundle.

#### Phase 2: Push (Deploy)

Deploys the following to the Android device at `/data/local/tmp/<Package>PackageTests-<arch>/`:

| Component | Source | Skip Flag |
|---|---|---|
| **Test binary** | `.build/<target>/<config>/<Package>PackageTests.xctest` | *(always pushed)* |
| **Project shared libraries** | `.build/<target>/<config>/*.so` | *(always pushed)* |
| **Swift runtime libraries** | `$SWIFT_ANDROID_SDK_HOME/swift-android/swift-resources/usr/lib/swift-<arch>/android/*.so*` | `--skip-push-stdlib` |
| **C++ standard library** | `$SWIFT_ANDROID_SDK_HOME/swift-android/ndk-sysroot/usr/lib/<ndk-triple>/libc++_shared.so` | `--skip-push-stdlib` |
| **External dependency libs** | `.build/artifacts/*/*/*/<triple>/*.so` | `--skip-push-external` |

#### Phase 3: Execute

Runs the test binary on the device via `adb shell` with `LD_LIBRARY_PATH` set to the deployment directory. Any `X_ANDROID_*` host environment variables are forwarded as environment variables on the device.

### Examples

**Full build-push-run cycle:**

```bash
swift-android test
```

**Run all tests in a specific module:**

```bash
swift-android test -Xtest MyModuleTests
```

**Run all tests in a specific test class:**

```bash
swift-android test -Xtest MyModuleTests.SomeTestClass
```

**Run a specific test case:**

```bash
swift-android test -Xtest MyModuleTests.SomeTestClass/testSpecificCase
```

**Run on a specific device:**

```bash
swift-android test --device DEVICE_SERIAL
```

**Quick re-run (skip build and push):**

```bash
swift-android test --fast
```

**Deploy only:**

```bash
swift-android test --deploy
```

**Skip only the stdlib push (already on device):**

```bash
swift-android test --skip-push-stdlib
```

**Iterative development (rebuild, only push project libs):**

```bash
swift-android test --skip-push-stdlib --skip-push-external
```

**Build in release and test:**

```bash
swift-android test -Xbuild -c -Xbuild release
```

**Forward environment variables to the device:**

```bash
X_ANDROID_MY_DEBUG=1 X_ANDROID_TRACE_LEVEL=verbose swift-android test
```

---

## License

MIT License - Copyright (c) 2017 [Readdle Inc.](https://readdle.com)

See [LICENSE](LICENSE) for details.
