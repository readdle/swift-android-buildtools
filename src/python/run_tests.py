#!/usr/bin/env python
from __future__ import print_function
from utils import *
from resources import copy_resources


self_dir = os.path.dirname(__file__)
swift_build = os.path.join(self_dir, "swift-build")


def push(dst, name, skip_push_stdlib, skip_push_external, skip_push_resources, device=None):
    from os.path import join
    from glob import glob

    ADB.makedirs(dst, device)

    if not skip_push_resources:
        copy_resources(device)

    if not skip_push_stdlib:
        ADB.push(dst, glob(join(SWIFT_ANDROID_HOME, "toolchain/usr/lib/swift/android", BuildConfig.swift_abi(), "*.so")), device)

    if not skip_push_external:
        ADB.push(dst, glob(join(Dirs.external_libs_dir(), "*.so")), device)

    ADB.push(dst, glob(join(Dirs.build_dir(), "*.so")), device)
    ADB.push(dst, [join(Dirs.build_dir(), name)], device)


def exec_tests(folder, name, args, device=None):
    ld_path = "LD_LIBRARY_PATH=" + folder
    test_path = folder + "/" + name

    ADB.shell([ld_path, test_path] + args, device)


def run(args):
    skip_build = args.skip_build or args.fast_mode
    skip_push = args.skip_push or args.fast_mode
    skip_push_stdlib = args.skip_push_stdlib
    skip_push_external = args.skip_push_external
    skip_push_resources = args.skip_push_resources

    skip_testing = args.skip_testing

    if not skip_build:
        sh_checked(
            [swift_build, "--build-tests"] + args.build_args
        )

    name = TestingApp.get_name()
    folder = TestingApp.get_folder(name)

    if not skip_push:
        push(folder, name, skip_push_stdlib, skip_push_external, skip_push_resources, args.device)

    if not skip_testing:
        exec_tests(folder, name, args.test_args, args.device)


def main():
    from arg_parser_ext import ArgumentParserOpt

    parser = ArgumentParserOpt(description="Build and run swift tests on Android")

    parser.add_argument(
        "-s", "--serial", "--device",
        dest="device",
        action="store",
        default=None,
        help="use device with given serial (overrides $ANDROID_SERIAL)"
    )

    parser.add_argument(
        "-f", "--fast", "--just-run",
        dest="fast_mode",
        action="store_true",
        default=False,
        help="Fast mode. Just run. Alias for --skip-build --skip-push"
    )

    parser.add_argument(
        "-d", "--deploy",
        dest="skip_testing",
        action="store_true",
        default=False,
        help="Build and push. Alias for --skip-testing"
    )

    parser.add_argument(
        "--skip-build",
        dest="skip_build",
        action="store_true",
        help="Skip rebuilding. Only deploy and run.",
    )

    parser.add_argument(
        "--skip-push",
        dest="skip_push",
        action="store_true",
        default=False,
        help="Skip rebuilding and redeploying. Just run."
    )

    parser.add_argument(
        "--skip-push-stdlib",
        dest="skip_push_stdlib",
        action="store_true",
        default=False,
        help="Don't push externally built libraries"
    )

    parser.add_argument(
        "--skip-push-external",
        dest="skip_push_external",
        action="store_true",
        default=False,
        help="Don't push toolchain libraries"
    )

    parser.add_argument(
        "--skip-testing",
        dest="skip_testing",
        action="store_true",
        default=False,
        help="Don't execute tests on device.\n"
             "Useful when you need build and deploy then run manually with different tool (simpleperf, lldb etc.)"
    )

    parser.add_argument(
        "--skip-push-resources",
        dest="skip_push_resources",
        action="store_true",
        default=False,
        help="Skip pushing resources to the device."
    )

    parser.add_argument(
        "-Xbuild",
        dest="build_args",
        action="append",
        default=[],
        help="Pass flag through to Swift PM"
    )

    parser.add_argument(
        "-Xtest",
        dest="test_args",
        action="append",
        default=[],
        help="Pass flag through to XCTest"
    )

    args = parser.parse_args()

    check_swift_home()
    run(args)


if __name__ == "__main__":
    main()
