#!/usr/bin/env python3

"""Detect Swift version from the SDK's sbom.spdx.json"""

import json
import os
import sys

DEFAULT_VERSION = "6.2"

def detect(sdk_home):
    sbom_path = os.path.join(sdk_home, "sbom.spdx.json")
    if os.path.exists(sbom_path):
        try:
            with open(sbom_path) as f:
                sbom = json.load(f)
            for package in sbom.get("packages", []):
                if package.get("name") == "swift":
                    version = package.get("versionInfo", "")
                    # Strip suffix like "-RELEASE" so "6.3-RELEASE" becomes "6.3"
                    version = version.split("-")[0]
                    parts = version.split(".")
                    if len(parts) >= 2:
                        return "{}.{}".format(parts[0], parts[1])
        except (IOError, json.JSONDecodeError, KeyError) as e:
            print("Warning: failed to parse {}: {}".format(sbom_path, e), file=sys.stderr)
    return DEFAULT_VERSION

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(DEFAULT_VERSION)
    else:
        print(detect(sys.argv[1]))
