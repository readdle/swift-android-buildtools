from utils import *
import os
from os import path
import json
from glob import glob

def is_glob(path):
    return "*" in path or "?" in path
class CopyCommand(object):
    def __init__(self):
        self.from_folder = ""
        self.into_folder = ""

    @classmethod
    def load_commands(cls, line):
        def wrap(prop):
            if prop is None:
                return []
            elif isinstance(prop, (str, unicode)):
                return [prop]
            elif isinstance(prop, (list, tuple)):
                return prop

        def get_or_default(obj, field, default=""):
            if field in obj:
                return obj[field]
            return default

        commands = []
        includes = get_or_default(line, 'include', None)

        if includes is not None and get_or_default(line, "into", None) is None:
            print("You need to pass `into` if you pass `include` line %s" % json.dumps(line))
            exit(1)

        from_ = get_or_default(line, 'from', line)


        into = get_or_default(line, "into", ".")

        exclude = wrap(get_or_default(line, "exclude", None))
        FROM_PATH = from_

        # Multiplication `from` * `include`, i.e. [from|include1, from|include2, from|include3]
        if includes is not None:
            froms = []
            for include in includes:
                froms.append(path.join(from_, include))
            from_ = froms
        else:
            from_ = wrap(from_)


        # Iterate each `from` folder, after multiplication
        for f in from_:
            command = CopyCommand()
            command.into_folder = into


            if len(exclude) == 0:
                if is_glob(f):
                    command.from_folder = glob(f)
                else:
                    command.from_folder = [f]
                commands.append(command)
            else:
                # Expand folder. Retrieve all files recursively
                froms = get_all_files_rec(glob(f))

                for copy in froms:
                    command = CopyCommand()
                    command.into_folder = path.normpath(path.join(into, copy['into']))
                    command.from_folder = copy['files']

                    from_folder_len = len(command.from_folder)

                    for excl in exclude:
                        def filter_path(p):
                            subpath = is_subpath(p, path.join(FROM_PATH, excl))

                            if subpath:
                                print "Excluding resource { %s }" % p
                                return False
                            return True

                        command.from_folder = filter(filter_path, command.from_folder)

                    if from_folder_len == len(command.from_folder) and copy['into'] != '.':  # Excluding file not here
                        command.from_folder = [path.join(copy['base'], copy['into'])]  # merge it back
                        command.into_folder = path.normpath(path.join(command.into_folder, path.pardir))

                    commands.append(command)
        return commands


def is_subpath(p, subpath):
    path_components = path.normpath(p).split(path.sep)  # ['a','b','c','d']
    subpath_components = path.normpath(subpath).split(path.sep)  # ['a','b']

    if len(path_components) < len(subpath_components):
        return False

    for i in range(len(subpath_components)):
        if path_components[i] != subpath_components[i]:
            return False
    return True


def get_all_files_rec(srcs):
    res = []
    for src in srcs:
        base = path.normpath(path.join(src, path.pardir))
        if path.isfile(src):
            res.append(
                {
                    "into": path.normpath(path.join(src[len(base) + 1:], path.pardir)),
                    "base": base,
                    "files": [src]
                }
            )
        else:
            for root, dirs, files in os.walk(src):
                if len(files) > 0:
                    res.append(
                        {  # TestData/Input/Resource1/file1, TestData/Input/Resource1/file2
                            "into": path.normpath(path.join(path.join(root, files[0])[len(base) + 1:], path.pardir)),
                        # Resource1
                            "base": base,  # TestData/Input/
                            "files": [path.join(root, f) for f in files]  # [file1, file2]
                        }
                    )

    return res


def copy_resources(device=None):
    """
    Copying resources to Android device by using `adb_push`

    It trying to find `resources.json` file inside `build-android-swift` folder,
    this file contains instructions, which file need to be adb_push to device

    Files will be located under `/data/local/tmp/${Testing Folder}/resources` -> `/data/local/tmp/${Testing Folder}/resources`

    """

    base_dir = Dirs.base_dir()

    copy_resources_filepath = path.join(base_dir, "build-android-swift/resources.json")

    if not os.path.exists(copy_resources_filepath):
        return
    else:
        print("Copy resources: %s is found!" % copy_resources_filepath)

    dst = path.join(TestingApp.get_app_folder(), "resources")

    # Clean
    ADB.shell(["rm", "-rf", dst], device)
    ADB.makedirs(dst, device)

    print("Copying resources...")

    resources = json.load(open(copy_resources_filepath))
    for line in resources:
        commands = CopyCommand.load_commands(line)
        for command in commands:
            dst_path = path.normpath(path.join(dst, command.into_folder))
            ADB.makedirs(dst_path, device)
            ADB.push(dst_path, command.from_folder, device)
