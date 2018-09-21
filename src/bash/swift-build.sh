#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
SELF_DIR=$SELF_DIR/src/bash

XCODE_SWIFTC=$(xcrun --find swiftc)
XCODE_SWIFT_BUILD=$(xcrun --find swift-build)

export CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang"
export SWIFT_EXEC=$SWIFT_ANDROID_HOME/toolchain/usr/bin/swiftc
export SWIFT_EXEC_MANIFEST=$XCODE_SWIFTC

include=-I.build/jniLibs/include
libs=-L.build/jniLibs/armeabi-v7a

flags="-Xcc $include -Xswiftc $include -Xswiftc $libs"

$XCODE_SWIFT_BUILD --destination=<($SELF_DIR/generate-destination-json.sh) $flags "$@"
exit $?