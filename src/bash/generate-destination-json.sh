#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
cat <<JSON > $SELF_DIR/$TARGET.json
{
    "version": 1,
    "dynamic-library-extension": "so",
    "toolchain-bin-dir": "$SWIFT_ANDROID_HOME/toolchain/usr/bin",
    "sdk": "$SWIFT_ANDROID_HOME/toolchain",
    "target": "$TARGET",
    
    "extra-cc-flags": [
        "-fPIC",
        "-I$SWIFT_ANDROID_HOME/toolchain/usr/lib/swift-$SWIFT_ANDROID_ARCH",
        "-I$SWIFT_ANDROID_HOME/toolchain/usr/include",
        "-I$SWIFT_ANDROID_HOME/toolchain/usr/include/$TRIPLE"
    ],
    "extra-swiftc-flags": [
        "-use-ld=lld",
        "-resource-dir", "$SWIFT_ANDROID_HOME/toolchain/usr/lib/swift-$SWIFT_ANDROID_ARCH",
        "-tools-directory", "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin",
        "-I$SWIFT_ANDROID_HOME/toolchain/usr/include",
        "-I$SWIFT_ANDROID_HOME/toolchain/usr/include/$TRIPLE"
    ],
    "extra-cpp-flags": [
        "-lstdc++"
    ]
}
JSON
