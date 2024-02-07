#!/bin/bash
: "${SWIFT_ANDROID_HOME:?$SWIFT_ANDROID_HOME should be set}"
: "${ANDROID_NDK_HOME:?$ANDROID_NDK_HOME should be set}"

SELF_DIR=$(dirname $0)
SELF_DIR=$SELF_DIR/src/bash

xcode_toolchain=$(dirname $(dirname $(dirname $(xcrun --find swift))))

export BUILD_ANDROID=1
ANDROID_API_LEVEL="${SWIFT_ANDROID_API_LEVEL:=24}"

export CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang"
export CXX="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/clang++"

# swiftc dont know about CC/CXX so tell correct compiler path for him in more brutal way
export PATH="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin:$PATH"

export SWIFT_EXEC=$SWIFT_ANDROID_HOME/toolchain/usr/bin/swiftc
export SWIFT_EXEC_MANIFEST=$xcode_toolchain/usr/bin/swiftc
export SWIFTPM_CUSTOM_LIBS_DIR=$xcode_toolchain/usr/lib/swift/pm

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

flags="-Xcc $include -Xswiftc $include -Xswiftc $libs -Xmanifest -DTARGET_ANDROID"

$SELF_DIR/generate-destination-json.sh
$SWIFT_ANDROID_HOME/toolchain/usr/bin/swift-build --destination=$SELF_DIR/$TARGET.json $flags "$@"

exit $?
