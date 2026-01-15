#!/bin/bash

ANDROID_API_LEVEL="${SWIFT_ANDROID_API_LEVEL:=31}"

if [ ! -n "${SWIFT_ANDROID_ARCH+defined}" ] || [ "$SWIFT_ANDROID_ARCH" == "aarch64" ]
then
    TRIPLE_FLAG=TRIPPLE_AARCH64_LINUX_ANDROID
elif [ "$SWIFT_ANDROID_ARCH" == "x86_64" ]
then
    TRIPLE_FLAG=TRIPPLE_X86_64_LINUX_ANDROID
elif [ "$SWIFT_ANDROID_ARCH" == "armv7" ]
then
    TRIPLE_FLAG=TRIPPLE_ARM_LINUX_ANDROID
elif [ "$SWIFT_ANDROID_ARCH" == "i686" ]
then
    TRIPLE_FLAG=TRIPPLE_I686_LINUX_ANDROID
else
    echo "Unknown arch '$SWIFT_ANDROID_ARCH'"
    exit 1
fi

flags="-Xbuild-tools-swiftc -DTARGET_ANDROID -Xbuild-tools-swiftc -D$TRIPLE_FLAG"
swiftly run +6.2 swift build --swift-sdk aarch64-unknown-linux-android$ANDROID_API_LEVEL $flags "$@"

exit $?
