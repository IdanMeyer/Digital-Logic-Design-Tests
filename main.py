#!/usr/bin/python

import os
import argparse

from infra.Exceptions import InfraException, TestFailedException
from infra.test_runners import ProjectTestsRunner

project_circuts_mapping = {
    "introduction": ["ztor", "pf4", "tautology", "parity", "ztand"],
    "graycode": ["g2b1", "g2b2", "g2b3", "g2b4"],
}

TESTS_RUNNER_DIR = "TestsRunner"
def _get_project_name_from_tests_runner_dir(circ_path=None):
    if not circ_path:
        circ_files = [file_name for file_name in os.listdir(TESTS_RUNNER_DIR) if file_name.endswith(".circ")]
        if len(circ_files) == 0:
            raise InfraException("Could not find .circ file. Make sure it is placed at TestsRunner")
        if len(circ_files) > 1:
            raise InfraException(
                "More than 1 .circ file found. Make sure you have exactly 1 .circ file at {}".format(TESTS_RUNNER_DIR))


        circ_path = os.path.join(TESTS_RUNNER_DIR, circ_files[0])

    circ_path_without_ext = os.path.splitext(circ_path)[0]

    project_name = None
    for name in project_circuts_mapping.keys():
        if name in circ_path_without_ext:
            project_name = name

    if not project_name:
        split_data = circ_path_without_ext.split("_")
        if 3 != len(split_data):
            raise InfraException("Invalid circ file: {}".format(circ_path))

        project_name = os.path.splitext(split_data[2])[0]

    return project_name, circ_path


def main(args):
    project_name, circ_path = _get_project_name_from_tests_runner_dir(args.circ)
    print("Testing project: {}".format(project_name))
    print("Testing circ file: {}".format(circ_path))
    if project_name not in project_circuts_mapping.keys():
        raise InfraException("Invalid project name parsed from .circ\nFile name {}.\nSupported projects: {}".format(
            circ_path,
            list(project_circuts_mapping.keys())))
    if args.circuit != None:
        circuits_names = [args.circuit]
    else:
        circuits_names = project_circuts_mapping[project_name]


    project_runner = ProjectTestsRunner(circ_path, project_name, circuits_names)
    try:
        project_runner.run()
    except TestFailedException as e:
        print(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test logisim circuits')
    parser.add_argument('--circ',  default=None,
                        help="Specify custom .circ file. By default, a circ file would be taken from TestsRunner dir")
    parser.add_argument('--circuit',  default=None,
                        help="Specify custom circuit that would be executed, instead of all supported")

    args = parser.parse_args()
    main(args)