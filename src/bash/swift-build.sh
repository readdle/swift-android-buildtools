#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
SELF_DIR=$SELF_DIR/src/bash

XCODE_SWIFTC=$(xcrun --find swiftc)

export CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang"
export SWIFT_EXEC=$SWIFT_ANDROID_HOME/toolchain/usr/bin/swiftc
export SWIFT_EXEC_MANIFEST=$XCODE_SWIFTC

if [ ! -n "${SWIFT_ANDROID_ARCH+defined}" ] || [ "$SWIFT_ANDROID_ARCH" == "aarch64" ]
then
    export TARGET=aarch64-none-linux-android
    export TRIPLE=aarch64-linux-android
    export ARCH=arm64
    export ABI=arm64-v8a
    export TOOLCHAIN_ROOT=aarch64-linux-android
elif [ "$SWIFT_ANDROID_ARCH" == "x86_64" ]
then
    export TARGET=x86_64-none-linux-android
    export TRIPLE=x86_64-linux-android
    export ARCH=x86_64
    export ABI=x86_64
    export TOOLCHAIN_ROOT=x86_64
elif [ "$SWIFT_ANDROID_ARCH" == "armv7" ]
then
    export TARGET=armv7-unknown-linux-androideabi
    export TRIPLE=arm-linux-androideabi
    export ARCH=arm
    export ABI=armeabi-v7a
    export TOOLCHAIN_ROOT=arm-linux-androideabi
elif [ "$SWIFT_ANDROID_ARCH" == "x86" ]
then
    export TARGET=i686-none-linux-android
    export TRIPLE=i686-linux-android
    export ARCH=x86
    export ABI=x86
    export TOOLCHAIN_ROOT=x86
else
    echo "Unknown arch '$SWIFT_ANDROID_ARCH'"
    exit 1
fi

include=-I.build/jniLibs/include
libs=-L.build/jniLibs/$ABI

flags="-Xcc $include -Xswiftc $include -Xswiftc $libs"

$SWIFT_ANDROID_HOME/toolchain/usr/bin/swift-build --destination=<($SELF_DIR/generate-destination-json.sh) $flags "$@"

exit $?
