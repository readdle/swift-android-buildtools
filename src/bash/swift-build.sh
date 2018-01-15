#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
SELF_DIR=$SELF_DIR/src/bash

export PATH="$SWIFT_ANDROID_HOME/toolchain/usr/bin:$PATH"
export CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang"
export SWIFT_EXEC=$SELF_DIR/swiftc-android.sh

include=-I.build/jniLibs/include
libs=-L.build/jniLibs/armeabi-v7a

flags="-Xcc $include -Xswiftc $include -Xswiftc $libs"

$SWIFT_ANDROID_HOME/toolchain/usr/bin/swift-build --destination=<($SELF_DIR/generate-destination-json.sh) $flags "$@"
exit $?
