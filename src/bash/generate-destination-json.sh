#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

EXTERNAL_TOOLCHAIN="$ANDROID_NDK_HOME/toolchains/$TOOLCHAIN_ROOT-4.9/prebuilt/darwin-x86_64"

cat <<JSON
{
    "version": 1,
    "dynamic-library-extension": "so",

    "target": "$TARGET",
    "sdk": "$ANDROID_NDK_HOME/platforms/android-23/arch-$ARCH",
    "toolchain-bin-dir": "$SWIFT_ANDROID_HOME/toolchain/usr/bin",

    "extra-swiftc-flags": [
        "-use-ld=gold", 
        "-Xfrontend", "-experimental-disable-objc-attr",
        "-tools-directory", "$EXTERNAL_TOOLCHAIN/$TRIPLE/bin",
        "-I$ANDROID_NDK_HOME/sysroot/usr/include",
        "-I$ANDROID_NDK_HOME/sysroot/usr/include/$TRIPLE",
        "-L$EXTERNAL_TOOLCHAIN/lib/gcc/$TRIPLE/4.9.x",
        "-L$ANDROID_NDK_HOME/sources/cxx-stl/llvm-libc++/libs/$ABI"
    ],
    "extra-cc-flags": [
        "-fPIC",
        "-fblocks",
        "--sysroot", "$ANDROID_NDK_HOME/sysroot",
        "-isystem", "$ANDROID_NDK_HOME/sysroot/usr/include/$TRIPLE",
        "-cxx-isystem", "$ANDROID_NDK_HOME/sources/cxx-stl/llvm-libc++/include",
        "-I$SWIFT_ANDROID_HOME/toolchain/usr/lib/swift"
    ],
    "extra-cpp-flags": [
        "-lc++_shared"
    ]
}
JSON
