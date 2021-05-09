import os
import subprocess
import re

class BaseExeception(Exception):
    pass

class TestFailedExeception(BaseExeception):
    pass

class CircutTestVectorRunner(object):
    LOGISIM_PATH = "Dependencies/logisim-2.7.2-cs3410-20140215.jar"

    def __init__(self, circ_path, project_name, circuit_name):
        self.circ_path = circ_path
        self.project_name = project_name
        self.circut_name = circuit_name

    def _validate_output(self, output):
        str_output, total_tests, passed, failed = self._parse_output(output)
        if int(failed) > 0:
            raise TestFailedExeception("\n\n\n{} - {} tests have failed.\nFull output:\n{}".format(
                self.circut_name,
                int(failed),
                str_output
            ))
        return str_output

    def _parse_output(self, output):
        str_output = output.stdout.decode("utf-8")
        total_tests = re.search("Running (\d+) vectors", str_output).group(1)
        passed = re.search("Passed: (\d+)", str_output).group(1)
        failed = re.search("Failed: (\d+)", str_output).group(1)

        print("Total Tests:", total_tests)
        print("Passed:", passed)
        print("Failed:", failed)

        return str_output, total_tests, passed, failed

    def _get_test_vector_path(self):
        return os.path.join("TestVectors",
                            self.project_name,
                            "test_vector_{}.txt".format(self.circut_name))

    def run(self):
        output = subprocess.run(["java",
                        "-jar",
                        type(self).LOGISIM_PATH,
                        self.circ_path,
                        "-test",
                        self.circut_name,
                        self._get_test_vector_path(),
                        ], stdout=subprocess.PIPE)
        return self._validate_output(output)

project_name = "Project1"
circut_name = "ztor"
bla = CircutTestVectorRunner(circ_path, project_name, circut_name)
bla.run()

