"""
Takes a Git diff on stdin, outputs a JSON representation.
"""

import os.path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import fileinput
import json

import gitdiffparser

print json.dumps(
    list(gitdiffparser.iter_files(fileinput.input())),
    indent=4
)
