#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
SELF_DIR=$SELF_DIR/src/bash

export PATH="$SWIFT_ANDROID_HOME/toolchain/usr/bin:$PATH"
export CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang"
export SWIFT_EXEC=$SELF_DIR/swiftc-android.sh

# all dynamic lookup should be done here
# because of strange sandbox like environment
# inside Swift PM called scripts
export _XCODE_SWIFT=$(xcrun --find swift)
export _XCODE_TOOLCHAIN=$(dirname $(dirname $(dirname $_XCODE_SWIFT)))

include=-I.build/jniLibs/include
libs=-L.build/jniLibs/armeabi-v7a

flags="-Xcc $include -Xswiftc $include -Xswiftc $libs"

$SWIFT_ANDROID_HOME/toolchain/usr/bin/swift-build --destination=<($SELF_DIR/generate-destination-json.sh) $flags "$@"
exit $?
