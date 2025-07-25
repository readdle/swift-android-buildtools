import json
import os
import subprocess
import sys

SWIFT_ANDROID_HOME = os.getenv("SWIFT_ANDROID_HOME")

def find_swift_toolchain():
    # Check common locations for Swift 6.1 toolchain
    toolchain_paths = [
        os.path.expanduser("~/Library/Developer/Toolchains/swift-6.1-RELEASE.xctoolchain"),
        "/Library/Developer/Toolchains/swift-6.1-RELEASE.xctoolchain"
    ]
    
    for path in toolchain_paths:
        if os.path.isdir(path):
            return path
            
    raise Exception("Swift 6.1 toolchain not found. Please install it from https://www.swift.org/install/macos")

def get_swift_command():
    toolchain = find_swift_toolchain()
    return os.path.join(toolchain, "usr/bin/swift")

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

# Kostyl. JSON should not be miixed with package resolution output.
def _filter_json(json_string):
    json_lines = json_string.split("\n")
    json_lines_filtered = []

    for line in json_lines:
        if line.startswith("Updating"):
            continue

        if len(line) == 0:
            continue

        json_lines_filtered.append(line)

    return "\n".join(json_lines_filtered)


@memoized
def _get_packages_tree():
    os_env = os.environ.copy()
    os_env["BUILD_ANDROID"] = "1"

    json_output = subprocess.check_output([
        get_swift_command(), "package", "show-dependencies", "-Xbuild-tools-swiftc", "-DTARGET_ANDROID", "--format", "json"
    ], env = os_env)

    if sys.version_info.major >= 3:
        json_output = json_output.decode()

    json_output = _filter_json(json_output)

    try:
        return json.loads(json_output)
    except:
        print("Bad json:")
        print(json_output)
        raise


@memoized
def get_package_description():
    os_env = os.environ.copy()
    os_env["BUILD_ANDROID"] = "1"

    json_output = subprocess.check_output([
        get_swift_command(), "package", "dump-package", "-Xbuild-tools-swiftc", "-DTARGET_ANDROID"
    ], env=os_env)

    return json.loads(json_output)

class BuildConfig(object):
    __configuration = "debug"

    @classmethod
    def setup(cls, configuration):
        allowed_configurations = ["release", "debug"]

        if configuration in allowed_configurations:
            cls.__configuration = configuration

    @classmethod
    @memoized
    def target(cls):
        arch = os.environ.get("SWIFT_ANDROID_ARCH")
        level = os.environ.get("SWIFT_ANDROID_API_LEVEL", "29")

        if arch == "aarch64" or arch is None:
            return "aarch64-unknown-linux-android{}".format(level)
        if arch == "x86_64":
            return "x86_64-unknown-linux-android{}".format(level)
        elif arch == "armv7":
            return "armv7-unknown-linux-androideabi{}".format(level)
        elif arch == "i686":
            return "i686-unknown-linux-android{}".format(level)
        else:
            raise Exception("Unknown arch '{}'".format(arch))

    @classmethod
    @memoized
    def tripple(cls):
        arch = os.environ.get("SWIFT_ANDROID_ARCH")

        if arch == "aarch64" or arch is None:
            return "aarch64-linux-android"
        if arch == "x86_64":
            return "x86_64-linux-android"
        elif arch == "armv7":
            return "armv7-linux-androideabi"
        elif arch == "i686":
            return "i686-linux-android"
        else:
            raise Exception("Unknown arch '{}'".format(arch))

    @classmethod
    @memoized
    def abi(cls):
        arch = os.environ.get("SWIFT_ANDROID_ARCH")

        if arch == "aarch64" or arch is None:
            return "arm64-v8a"
        elif arch == "x86_64":
            return "x86_64"
        elif arch == "armv7":
            return "armeabi-v7a"
        elif arch == "i686":
            return "x86"
        else:
            raise Exception("Unknown arch '{}'".format(arch))

    @classmethod
    @memoized
    def swift_abi(cls):
        arch = os.environ.get("SWIFT_ANDROID_ARCH")

        if arch == "aarch64" or arch is None:
            return "aarch64"
        elif arch == "x86_64":
            return "x86_64"
        elif arch == "armv7":
            return "armv7"
        elif arch == "i686":
            return "i686"
        else:
            raise Exception("Unknown arch '{}'".format(arch))


    @classmethod
    def configuration(cls):
        return cls.__configuration

    @classmethod
    def is_debug(cls):
        return cls.configuration() == "debug"


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
        return os.path.join(cls.build_root(), BuildConfig.target(), BuildConfig.configuration())

    @classmethod
    @memoized
    def external_out_dir(cls):
        return os.path.join(cls.build_root(), "artifacts/*/*/*")

    @classmethod
    @memoized
    def external_libs_dir(cls):
        return os.path.join(cls.external_out_dir(), BuildConfig.tripple())

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
        name = name.split(".")[0]
        abi = BuildConfig.swift_abi()
        return "/data/local/tmp/{}-{}".format(name, abi)

    @classmethod
    def get_app_folder(cls):
        return cls.get_folder(cls.get_name())

class ADB(object):
    @classmethod
    def push(cls, dst, files, device=None):
        if isinstance(files, list) and len(files) != 0:
            sh_checked(cls._base_args(device) + ["push"] + files + [dst])

    @classmethod
    def shell(cls, args, device=None):
        env = []

        for key, value in os.environ.items():
            if key.startswith("X_ANDROID"):
                name = key[len("X_ANDROID_"):]
                env.append(name + "=" + value)

        sh_checked(cls._base_args(device) + ["shell"] + env + args)

    @classmethod
    def makedirs(cls, dir, device=None):
        cls.shell(["mkdir", "-p", dir], device)
        cls.shell(["chmod", "777", dir], device)

    @classmethod
    def _base_args(cls, device):
        return ["adb"] + cls._device_args(device)

    @classmethod
    def _device_args(cls, device):
        if device is None:
            return []
        else:
            return ["-s", device]


def copytree(src, dst):
    from glob import glob

    src_files = glob(src)

    if len(src_files) == 0:
        return

    subprocess.call(["rsync", "-a"] + src_files + [dst])


def check_swift_home():
    if SWIFT_ANDROID_HOME is None or not os.path.isdir(SWIFT_ANDROID_HOME):
        print("SWIFT_ANDROID_HOME not set execution stopped")
        sys.exit(127)

