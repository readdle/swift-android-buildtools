#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

cat <<JSON
{
    "version": 1,
    "dynamic-library-extension": "so",

    "target": "armv7-unknown-linux-androideabi",
    "sdk": "$SWIFT_ANDROID_HOME/toolchain/ndk-android-21",
    "toolchain-bin-dir": "$SWIFT_ANDROID_HOME/toolchain/usr/bin",

    "extra-swiftc-flags": [
        "-use-ld=gold", 
        "-tools-directory", 
        "$SWIFT_ANDROID_HOME/toolchain/usr/bin",
        "-L$SWIFT_ANDROID_HOME/toolchain/usr/bin"
    ],
    "extra-cc-flags": [
        "-fPIC",
        "-fblocks",
        "-I$ANDROID_NDK_HOME/sources/cxx-stl/llvm-libc++/include",
        "-I$SWIFT_ANDROID_HOME/toolchain//usr/lib/swift"
    ],
    "extra-cpp-flags": [
        "-lc++_shared"
    ]
}
JSON