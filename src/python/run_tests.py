#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from utils import *
from resources import copy_resources
from build import swift_build


def push(dst, name, skip_push_stdlib, skip_push_external, skip_push_resources, device=None):
    from os.path import join
    from glob import glob

    ADB.makedirs(dst, device)

    if not skip_push_resources:
        copy_resources(device)

    if not skip_push_stdlib:
        ADB.push(dst, glob(join(SWIFT_ANDROID_SDK_HOME, "swift-android/swift-resources/usr/lib/swift-{}/android/".format(BuildConfig.swift_abi()), "*.so*")), device)
        ADB.push(dst, glob(join(SWIFT_ANDROID_SDK_HOME, "swift-android/ndk-sysroot/usr/lib/{}/".format(BuildConfig.ndk_triple()), "libc++_shared.so")), device)

    if not skip_push_external:
        ADB.push(dst, glob(join(Dirs.external_libs_dir(), "*.so")), device)

    ADB.push(dst, glob(join(Dirs.build_dir(), "*.so")), device)
    ADB.push(dst, [join(Dirs.build_dir(), name)], device)


def exec_tests(folder, name, args, device=None):
    ld_path = "LD_LIBRARY_PATH=" + folder
    test_path = folder + "/" + name

    ADB.shell([ld_path, test_path] + args, device)


def _exec_tests_capture(folder, name, args, device=None):
    """Run tests and capture stdout. Returns (exit_code, stdout_str)."""
    ld_path = "LD_LIBRARY_PATH=" + folder
    test_path = folder + "/" + name

    env = []
    for key, value in os.environ.items():
        if key.startswith("X_ANDROID"):
            env_name = key[len("X_ANDROID_"):]
            env.append(env_name + "=" + value)

    cmd = ADB._base_args(device) + ["shell"] + env + [ld_path, test_path] + args
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = process.communicate()

    if sys.version_info.major >= 3:
        stdout = stdout.decode()

    return process.returncode, stdout


def list_test_classes(folder, name, device=None):
    """Query the test binary for all available test classes via --dump-tests-json."""
    ld_path = "LD_LIBRARY_PATH=" + folder
    test_path = folder + "/" + name

    output = ADB.shell_output([ld_path, test_path, "--dump-tests-json"], device)
    output = output.strip()

    if not output:
        print("Error: --dump-tests-json returned empty output", file=sys.stderr)
        sys.exit(1)

    json_start = output.find("{")
    if json_start > 0:
        output = output[json_start:]

    try:
        tests_json = json.loads(output)
    except json.JSONDecodeError:
        print("Error: --dump-tests-json returned invalid JSON:", file=sys.stderr)
        print(output[:500], file=sys.stderr)
        sys.exit(1)

    classes = []
    for test_suite in tests_json.get("tests", []):
        for test_class in test_suite.get("tests", []):
            class_name = test_class.get("name", "")
            if class_name:
                classes.append(class_name)
    return classes


_EXECUTED_RE = re.compile(
    r"Executed (\d+) tests?, with (\d+) failures? \((\d+) unexpected\) in ([\d.]+) \(([\d.]+)\) seconds"
)


def _parse_xctest_summary(output):
    """Extract test counts from XCTest output. Returns (executed, failures, unexpected, wall_time)."""
    for line in reversed(output.splitlines()):
        m = _EXECUTED_RE.search(line)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(5))
    return 0, 0, 0, 0.0


def _filter_class_output(output):
    """Strip the 'Selected tests' suite wrapper so per-class output can be unified."""
    lines = output.splitlines(True)
    filtered = []
    skip_next_executed = False
    for line in lines:
        if "Test Suite 'Selected tests'" in line:
            skip_next_executed = True
            continue
        if skip_next_executed and "Executed" in line:
            skip_next_executed = False
            continue
        skip_next_executed = False
        filtered.append(line)
    return "".join(filtered)


def exec_tests_sequential(folder, name, test_args, device=None):
    """Run each test class in its own process and aggregate results.

    When test_args contains filters, each filter is run in its own process
    instead of discovering classes automatically.
    """
    if test_args:
        classes = test_args
    else:
        classes = list_test_classes(folder, name, device)

    if not classes:
        print("No test classes found!")
        sys.exit(1)

    start_time = time.time()

    failed_classes = []
    crashed_classes = []

    for cls_name in classes:
        exit_code, output = _exec_tests_capture(folder, name, [cls_name], device)

        sys.stdout.write(_filter_class_output(output))
        sys.stdout.flush()

        if exit_code != 0:
            executed, _, _, _ = _parse_xctest_summary(output)
            if executed > 0:
                failed_classes.append(cls_name)
            else:
                crashed_classes.append(cls_name)

    elapsed = time.time() - start_time
    total = len(classes)
    bad = len(failed_classes) + len(crashed_classes)
    passed = total - bad

    status = "passed" if bad == 0 else "failed"

    parts = ["{} passed".format(passed)]
    if failed_classes:
        parts.append("{} failed".format(len(failed_classes)))
    if crashed_classes:
        parts.append("{} crashed".format(len(crashed_classes)))

    print("Test Suite 'All tests' {}".format(status))
    print("\t Executed {} test suites: {} in {:.3f} seconds".format(
        total, ", ".join(parts), elapsed
    ))

    if crashed_classes:
        print("\nCrashed test suites:")
        for cls_name in crashed_classes:
            print("  - {}".format(cls_name))

    if failed_classes or crashed_classes:
        sys.exit(1)


def run(args):
    skip_build = args.skip_build or args.fast_mode
    skip_push = args.skip_push or args.fast_mode
    skip_push_stdlib = args.skip_push_stdlib
    skip_push_external = args.skip_push_external
    skip_push_resources = args.skip_push_resources

    skip_testing = args.skip_testing

    if not skip_build:
        swift_build(["--build-tests"] + args.build_args)

    name = TestingApp.get_name()
    folder = TestingApp.get_folder(name)

    if not skip_push:
        push(folder, name, skip_push_stdlib, skip_push_external, skip_push_resources, args.device)

    if not skip_testing:
        if args.isolate:
            exec_tests_sequential(folder, name, args.test_args, args.device)
        else:
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
        "--isolate",
        dest="isolate",
        action="store_true",
        default=False,
        help="Run each test class in its own process for crash isolation.\n"
             "A crash in one class won't prevent remaining classes from running."
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

