#!/usr/bin/python

import os
import tempfile

from infra.Exceptions import InfraException, TestFailedException
from infra.test_runners import ProjectTestsRunner

project_circuts_mapping = {
    "introduction": ["ztor", "pf4"]
    # "introduction": ["pf4"]
}

TESTS_RUNNER_DIR = "TestsRunner"
def _get_project_name_from_tests_runner_dir():
    circ_files = [file_name for file_name in os.listdir(TESTS_RUNNER_DIR) if file_name.endswith(".circ")]
    if len(circ_files) == 0:
        raise InfraException("Could not find .circ file")
    if len(circ_files) > 1:
        raise InfraException(
            "More than 1 .circ file found. Make sure you have exactly 1 .circ file at {}".format(TESTS_RUNNER_DIR))

    file_name = circ_files[0]
    file_name_without_ext = os.path.splitext(file_name)[0]
    split_data = file_name_without_ext.split("_")
    if 3 != len(split_data):
        raise InfraException("Invalid circ file: {}".format(file_name))

    project_name = os.path.splitext(split_data[2])[0]
    return project_name, os.path.join(TESTS_RUNNER_DIR, file_name)

project_name, circ_path = _get_project_name_from_tests_runner_dir()
print("Testing project: {}".format(project_name))
print("Testing circ file: {}".format(circ_path))

if project_name not in project_circuts_mapping.keys():
    raise InfraException("Invalid project name parsed from .circ\nFile name {}.\nSupported projects: {}".format(
        circ_path,
        list(project_circuts_mapping.keys())))
circuts_names = project_circuts_mapping[project_name]


project_runner = ProjectTestsRunner(circ_path, project_name, circuts_names)
try:
    project_runner.run()
except TestFailedException as e:
    print(e)
