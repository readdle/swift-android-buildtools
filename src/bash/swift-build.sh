#!/bin/bash

export BUILD_ANDROID=1
ANDROID_API_LEVEL="${SWIFT_ANDROID_API_LEVEL:=31}"

if [ ! -n "${SWIFT_ANDROID_ARCH+defined}" ] || [ "$SWIFT_ANDROID_ARCH" == "aarch64" ]
then
    export TRIPLE=aarch64-linux-android
    TRIPLE_FLAG=TRIPPLE_AARCH64_LINUX_ANDROID
elif [ "$SWIFT_ANDROID_ARCH" == "x86_64" ]
then
    export TRIPLE=x86_64-linux-android
    TRIPLE_FLAG=TRIPPLE_X86_64_LINUX_ANDROID
elif [ "$SWIFT_ANDROID_ARCH" == "armv7" ]
then
    export TRIPLE=arm-linux-androideabi
    TRIPLE_FLAG=TRIPPLE_ARM_LINUX_ANDROID
elif [ "$SWIFT_ANDROID_ARCH" == "i686" ]
then
    export TRIPLE=i686-linux-android
    TRIPLE_FLAG=TRIPPLE_I686_LINUX_ANDROID
else
    echo "Unknown arch '$SWIFT_ANDROID_ARCH'"
    exit 1
fi

flags="-Xbuild-tools-swiftc -DTARGET_ANDROID -Xbuild-tools-swiftc -D$TRIPLE_FLAG"
swiftly run swift build --swift-sdk aarch64-unknown-linux-android$ANDROID_API_LEVEL $flags "$@"

exit $?
