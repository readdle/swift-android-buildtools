#!/usr/bin/env python

from os import getenv

import collect_dependencies
from utils import *


def make_env(name):
    swift_lib = os.path.join(SWIFT_ANDROID_HOME, "toolchain", "usr", "lib", "swift")

    external_build_root = Dirs.external_build_root(name)
    external_out_dir = Dirs.external_out_dir()
    external_include_dir = Dirs.external_include_dir()

    pm_build_dir = Dirs.build_dir()

    mkdirs(swift_lib)
    mkdirs(external_build_root)
    mkdirs(external_out_dir)
    mkdirs(external_include_dir)
    mkdirs(pm_build_dir)

    if BuildConfig.is_debug():
        NDK_DEBUG = True
    else:
        NDK_DEBUG = False

    return {
        "NDK_DEBUG": str(int(NDK_DEBUG)),
        "SWIFT_LIB": swift_lib,
        "SWIFT_PM_EXTERNAL_BUILD_ROOT": external_build_root,
        "SWIFT_PM_EXTERNAL_LIBS": external_out_dir,
        "SWIFT_PM_EXTERNAL_INCLUDE": external_include_dir,
        "SWIFT_PM_BUILD_DIR": pm_build_dir,
    }


def get_script_path(base):
    return os.path.join(base, "build-android-swift", "invoke-external-build")


def is_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)


def invoke_external(path, name):
    script = get_script_path(path)

    if not is_executable(script):
        return

    sh_checked([script], env=make_env(name))


def run():
    collect_dependencies.run()
    traverse_dependencies(invoke_external, include_root=True)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument(
        "-c", "--configuration",
        default="debug",
        help="Build with configuration (debug|release) [default: debug]"
    )

    args = parser.parse_args()

    BuildConfig.setup(
        configuration=args.configuration
    )

    check_swift_home()
    run()
