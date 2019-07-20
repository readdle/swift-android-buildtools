#!/usr/bin/env python

from utils import *


def copy_prebuilt(src, libs_dir, include_dir):
    copytree(os.path.join(src, "libs", "*"), libs_dir)
    copytree(os.path.join(src, "include", "*"), include_dir)


def copy_prebuilt_task(module, name):
    libs_dir = Dirs.external_out_dir()
    include_dir = Dirs.external_include_dir()
    
    mkdirs(libs_dir)
    mkdirs(include_dir)
    copy_prebuilt(module, libs_dir, include_dir)


def run():
    traverse_dependencies(copy_prebuilt_task)


if __name__ == "__main__":
    run()
