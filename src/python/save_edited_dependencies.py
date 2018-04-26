#!/usr/bin/env python3
from __future__ import print_function

from utils import *
import json
import os
import sys
import subprocess
import copy
from collections import OrderedDict


class Dependency(object):
    def __init__(self, name, repository_url, base_state, path):
        if path is None:
            path = os.path.join(Dirs.base_dir(), "Packages", name)

        self.name = name
        self.repository_url = repository_url
        self.base_state = copy.copy(base_state)
        self.path = path

    @classmethod
    def from_json(cls, dependency_json):
        name = dependency_json["name"]
        repository_url = dependency_json["repositoryURL"]
        base_state = dependency_json["basedOn"]["state"]["checkoutState"]
        path = dependency_json["state"]["path"]

        return Dependency(name, repository_url, base_state, path)

    def to_pin(self):
        state = copy.copy(self.base_state)
        state["revision"] = self.git_hash()

        return OrderedDict([
            ("package", self.name),
            ("repositoryURL", self.repository_url),
            ("state", state)
        ])

    def git_hash(self):
        git_dir = os.path.join(self.path, ".git")
        output = subprocess.check_output(["git", "--git-dir", git_dir, "rev-parse", "HEAD"])
        return output.decode("utf-8").strip()


def get_state_json():
    build_root = Dirs.build_root()
    state_file = os.path.join(build_root, "dependencies-state.json")

    if not os.path.exists(state_file):
        print("dependencies-state.json not found")
        return None

    with open(state_file) as fd:
        return json.load(fd, encoding="utf-8", object_pairs_hook=OrderedDict)


def find_edited(json_root):
    dependencies_json = json_root["object"]["dependencies"]

    result = []

    for dependency_json in dependencies_json:
        if dependency_json["state"]["name"] == "edited":
            dependency = Dependency.from_json(dependency_json)
            result.append(dependency)

    return result


def store(dependencies):
    base_dir = Dirs.base_dir()
    package_resolved_path = os.path.join(base_dir, "Package.resolved")

    if not os.path.exists(package_resolved_path):
        print("Package.resolved not found")
        return

    with open(package_resolved_path, "r") as fd:
        package_resolved = json.load(fd, encoding="utf-8", object_pairs_hook=OrderedDict)

    pins = package_resolved["object"]["pins"]
    pins = process_pins(pins, dependencies)
    package_resolved["object"]["pins"] = pins

    with open(package_resolved_path, "w") as fd:
        json.dump(package_resolved, fd, indent=2, separators=(',', ': '))


def process_pins(pins, edited):
    edited_names = set()
    for dependency in edited:
        edited_names.add(dependency.name)

    pins = list(filter(lambda pin: pin["package"] not in edited_names, pins))

    for dependency in edited:
        pins.append(dependency.to_pin())

    return sorted(pins, key=lambda pin: pin["package"])


def main():
    state_json = get_state_json()
    if state_json is None:
        sys.exit(1)

    try:
        edited_dependencies = find_edited(state_json)
        store(edited_dependencies)
    except Exception as exc:
        print(exc.message)
        sys.exit(1)


if __name__ == "__main__":
    main()
