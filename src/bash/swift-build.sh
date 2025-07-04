#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
SELF_DIR=$SELF_DIR/src/bash

XCODE_TOOLCHAIN=~/Library/Developer/Toolchains/swift-6.1-RELEASE.xctoolchain

if [ ! -d "$XCODE_TOOLCHAIN" ]; then
    XCODE_TOOLCHAIN=/Library/Developer/Toolchains/swift-6.1-RELEASE.xctoolchain
fi

if [ ! -d "$XCODE_TOOLCHAIN" ]; then
    echo "Toolchain not found at $XCODE_TOOLCHAIN"
    echo "Please install the Swift 6.1 toolchain from https://www.swift.org/install/macos"
    exit 1
fi

export BUILD_ANDROID=1
ANDROID_API_LEVEL="${SWIFT_ANDROID_API_LEVEL:=28}"

export CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang"
export CXX="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang++"

if [ ! -n "${SWIFT_ANDROID_ARCH+defined}" ] || [ "$SWIFT_ANDROID_ARCH" == "aarch64" ]
then
    export SWIFT_ANDROID_ARCH=aarch64
    export TARGET=aarch64-unknown-linux-android${ANDROID_API_LEVEL}
    export TRIPLE=aarch64-linux-android
    export ABI=arm64-v8a
elif [ "$SWIFT_ANDROID_ARCH" == "x86_64" ]
then
    export SWIFT_ANDROID_ARCH=x86_64
    export TARGET=x86_64-unknown-linux-android${ANDROID_API_LEVEL}
    export TRIPLE=x86_64-linux-android
    export ABI=x86_64
elif [ "$SWIFT_ANDROID_ARCH" == "armv7" ]
then
    export SWIFT_ANDROID_ARCH=armv7
    export TARGET=armv7-unknown-linux-androideabi${ANDROID_API_LEVEL}
    export TRIPLE=arm-linux-androideabi
    export ABI=armeabi-v7a
elif [ "$SWIFT_ANDROID_ARCH" == "i686" ]
then
    export SWIFT_ANDROID_ARCH=i686
    export TARGET=i686-unknown-linux-android${ANDROID_API_LEVEL}
    export TRIPLE=i686-linux-android
    export ABI=x86
else
    echo "Unknown arch '$SWIFT_ANDROID_ARCH'"
    exit 1
fi

include=-I.build/jniLibs/include
libs=-L.build/jniLibs/$ABI

flags="-Xcc $include -Xswiftc $include -Xswiftc $libs -Xbuild-tools-swiftc -DTARGET_ANDROID"

$SELF_DIR/generate-destination-json.sh
$XCODE_TOOLCHAIN/usr/bin/swift-build --destination=$SELF_DIR/$TARGET.json $flags "$@"

exit $?
