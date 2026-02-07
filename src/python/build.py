#!/usr/bin/env python3

from utils import *


def swift_build(extra_args=None):
    """Run swift build for Android with the given extra arguments."""
    if extra_args is None:
        extra_args = []

    flags = [
        "-Xbuild-tools-swiftc", "-DTARGET_ANDROID",
        "-Xbuild-tools-swiftc", "-D{}".format(BuildConfig.triple_flag())
    ]

    cmd = [
        "swiftly", "run", "+{}".format(SWIFT_VERSION),
        "swift", "build",
        "--swift-sdk", BuildConfig.target()
    ] + flags + extra_args

    sh_checked(cmd)


def main():
    check_swift_home()
    swift_build(sys.argv[1:])


if __name__ == "__main__":
    main()
