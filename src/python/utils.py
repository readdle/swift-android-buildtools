from __future__ import print_function

import json
import os
import subprocess
import sys

SWIFT_ANDROID_HOME = os.getenv("SWIFT_ANDROID_HOME")

def memoized(func):
    state = type("State", (object,), {
        "called": False,
        "result": None
    })

    def wrapper(*args, **kvargs):
        if not state.called:
            state.result = func(*args, **kvargs)
            state.called = True

        return state.result

    return wrapper


def check_return_code(code):
    if code != 0:
        sys.exit(code)


def sh_checked(cmd, env=None):
    from subprocess import Popen

    if isinstance(env, dict):
        env = dict(os.environ, **env)

    process = Popen(cmd, env=env)
    code = process.wait()

    check_return_code(code)


def mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


@memoized
def _resolve_packages():
    sh_checked(['swift', 'package', 'resolve'])


@memoized
def _get_packages_tree():
    _resolve_packages()

    json_output = subprocess.check_output([
        "swift", "package", "show-dependencies", "--format", "json"
    ])

    return json.loads(json_output)


@memoized
def get_package_description():
    _resolve_packages()

    json_output = subprocess.check_output([
        "swift", "package", "dump-package"
    ])

    return json.loads(json_output)


def _traverse(root_node, include_root, func):
    seen = set()

    if not include_root:
        seen.add(root_node["path"])
    
    def inner(node):
        children = node["dependencies"]
        path = node["path"]
        name = node["name"]

        for sub_node in children:
            inner(sub_node)

        if path not in seen:
            func(path, name)
            seen.add(path)

    inner(root_node)


class BuildConfig(object):
    __configuration = "debug"

    @classmethod
    def setup(cls, configuration):
        allowed_configurations = ["release", "debug"]

        if configuration in allowed_configurations:
            cls.__configuration = configuration

    @classmethod
    @memoized
    def triple(cls):
        return "armv7-unknown-linux-androideabi"

    @classmethod
    @memoized
    def abi(cls):
        return "armeabi-v7a"

    @classmethod
    def configuration(cls):
        return cls.__configuration

    @classmethod
    def is_debug(cls):
        cls.configuration() == "debug"


class Dirs(object):
    @classmethod
    @memoized
    def base_dir(cls):
        root_node = _get_packages_tree()
        return root_node["path"]

    @classmethod
    @memoized
    def build_root(cls):
        return os.path.join(cls.base_dir(), ".build")

    @classmethod
    @memoized
    def build_dir(cls):
        return os.path.join(cls.build_root(), BuildConfig.triple(), BuildConfig.configuration())

    @classmethod
    def external_build_root(cls, name):
        return os.path.join(cls.build_root(), "external-build", name)

    @classmethod
    @memoized
    def external_out_dir(cls):
        return os.path.join(cls.build_root(), "jniLibs")

    @classmethod
    @memoized
    def external_include_dir(cls):
        return os.path.join(cls.external_out_dir(), "include")

    @classmethod
    @memoized
    def external_libs_dir(cls):
        return os.path.join(cls.external_out_dir(), BuildConfig.abi())

class TestingApp(object):
    @classmethod
    def extract_tests_package(cls, package):
        return package["name"] + "PackageTests.xctest"

    @classmethod
    def get_name(cls):
        package = get_package_description()
        return cls.extract_tests_package(package)

    @classmethod
    def get_folder(cls, name):
        return "/data/local/tmp/" + name.split(".")[0]

    @classmethod
    def get_app_folder(cls):
        return cls.get_folder(cls.get_name())

class ADB(object):
    @classmethod
    def push(cls, dst, files):
        for f in files:
            sh_checked(["adb", "push", f, dst])

    @classmethod
    def shell(cls, args):
        env = []

        for key, value in os.environ.iteritems():
            if key.startswith("X_ANDROID"):
                name = key[len("X_ANDROID_"):]
                env.append(name + "=" + value)

        sh_checked(["adb", "shell"] + env + args)

    @classmethod
    def makedirs(cls, dir):
        cls.shell(["mkdir", "-p", dir])


def traverse_dependencies(func, include_root=False):
    _traverse(_get_packages_tree(), include_root, func)


def copytree(src, dst):
    from glob import glob

    src_files = glob(src)

    if len(src_files) == 0:
        return

    subprocess.call(["rsync", "-r"] + src_files + [dst])


def check_swift_home():
    if SWIFT_ANDROID_HOME is None or not os.path.isdir(SWIFT_ANDROID_HOME):
        print("SWIFT_ANDROID_HOME not set execution stopped")
        sys.exit(127)
