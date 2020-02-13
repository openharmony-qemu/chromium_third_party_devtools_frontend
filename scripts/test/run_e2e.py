#!/usr/bin/env python
#
# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
Run tests on a pinned version of chrome.
"""

import argparse
import os
import re
from subprocess import Popen
import sys
import signal

scripts_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(scripts_path)

import devtools_paths
import test_helpers

is_cygwin = sys.platform == 'cygwin'


def parse_options(cli_args):
    parser = argparse.ArgumentParser(description='Run tests')
    parser.add_argument('--chrome-binary', dest='chrome_binary', help='path to Chromium binary')
    parser.add_argument('--test-suite', dest='test_suite', help='path to test suite')
    return parser.parse_args(cli_args)


def compile_typescript_test_files():
    cwd = devtools_paths.devtools_root_path()
    shared_path = os.path.join(cwd, 'test', 'shared')
    e2e_test_path = os.path.join(cwd, 'test', 'e2e')

    # Compile shared code, e.g. helper and runner.
    print("Compiling shared TypeScript")
    exec_command = [devtools_paths.node_path(), devtools_paths.typescript_compiler_path(), '-p', shared_path]
    exit_code = test_helpers.popen(exec_command)
    if exit_code != 0:
        print(exit_code)
        return True

    # Compile e2e tests, e.g. helper and runner.
    print("Compiling e2e TypeScript")
    exec_command = [devtools_paths.node_path(), devtools_paths.typescript_compiler_path(), '-p', e2e_test_path]
    exit_code = test_helpers.popen(exec_command)
    if exit_code != 0:
        return True

    return False


def run_browser_test(chrome_binary):
    cwd = devtools_paths.devtools_root_path()
    e2e_test_path = os.path.join(cwd, 'test', 'shared', 'runner.js')
    e2e_test_list = os.path.join(cwd, 'test', 'e2e', 'test-list.js')
    exec_command = [devtools_paths.node_path(), e2e_test_path]

    env = os.environ.copy()
    env['CHROME_BIN'] = chrome_binary
    env['TEST_LIST'] = e2e_test_list

    exit_code = test_helpers.popen(exec_command, cwd=cwd, env=env)
    if exit_code != 0:
        return True

    return False


def main():
    OPTIONS = parse_options(sys.argv[1:])
    is_cygwin = sys.platform == 'cygwin'
    chrome_binary = None

    # Default to the downloaded / pinned Chromium binary
    downloaded_chrome_binary = devtools_paths.downloaded_chrome_binary_path()
    if test_helpers.check_chrome_binary(downloaded_chrome_binary):
        chrome_binary = downloaded_chrome_binary

    # Override with the arg value if provided.
    if OPTIONS.chrome_binary:
        chrome_binary = OPTIONS.chrome_binary
        if not test_helpers.check_chrome_binary(chrome_binary):
            print('Unable to find a Chrome binary at \'%s\'' % chrome_binary)
            sys.exit(1)

    if (chrome_binary is None):
        print('Unable to run, no Chrome binary provided')
        sys.exit(1)

    print('Using Chromium binary (%s)\n' % chrome_binary)

    errors_found = False
    try:
        errors_found = compile_typescript_test_files()
        if (errors_found):
            raise Exception('Typescript failed to compile')
        errors_found = run_browser_test(chrome_binary)
    except Exception as err:
        print(err)

    if errors_found:
        print('ERRORS DETECTED')
        sys.exit(1)


if __name__ == '__main__':
    main()
