import os
import shutil
import subprocess
import re
import tempfile

from infra.Exceptions import TestFailedException

NEWLINE = "\n"


class CircutTestVectorRunner(object):
    LOGISIM_PATH = "Dependencies/logisim-evolution-3.4.1-all.jar"

    def __init__(self, circ_path, project_name, circuit_name):
        self.circ_path = circ_path
        self.project_name = project_name
        self.circut_name = circuit_name

    def _validate_output_test_vector(self, output):
        str_output, total_tests, passed, failed = self._parse_output_test_vector(output)
        if int(failed) > 0:
            raise TestFailedException("\n\n\n{} - {} tests have failed.\nFull output:\n{}".format(
                self.circut_name,
                int(failed),
                str_output
            ))
        print("{} - Passed".format(self.circut_name))
        return str_output

    def _parse_output_test_vector(self, output):
        str_output = output.stdout.decode("utf-8")
        total_tests = re.search("Running (\d+) vectors", str_output).group(1)
        passed = re.search("Passed: (\d+)", str_output).group(1)
        failed = re.search("Failed: (\d+)", str_output).group(1)

        return str_output, total_tests, passed, failed


    def _validate_output_tty_table(self, output):
        with open(self._get_test_vector_path()) as f:
            test_vector_data = f.read()

        output_data = output.stdout.decode("utf-8")
        passed, failed, error_lines = self._compare_output_and_test_vector(output_data, test_vector_data)

        # str_output, total_tests, passed, failed = self._parse_output_tty_table(output)
        if int(failed) > 0:
            raise TestFailedException("\n\n\n{} - {} tests have failed.\nFull output:\n{}".format(
                self.circut_name,
                int(failed),
                NEWLINE.join(error_lines)
            ))
        print("{} - Passed".format(self.circut_name))
        return error_lines

    def _compare_output_and_test_vector(self, output_data, test_vector_data):
        passed = 0
        failed = 0
        error_message = []

        # Remove comments and newlines
        NEWLINE = "\n"
        test_vector_data = NEWLINE.join([x for x in test_vector_data.split("\n") if
                                            not x.startswith("#") and x != ''])
        # Skip first line which contains the variables
        for test_vector_line, output_line in zip(test_vector_data.split(NEWLINE)[1:],
                                                 output_data.split(NEWLINE)[1:]):
            test_vector_vars = test_vector_line.split()
            output_vars = output_line.split()
            var_failed = False
            for test_vector_var, output_var in zip(test_vector_vars, output_vars):
                if test_vector_var != output_var:
                    error_message.append("{} | {}".format(" ".join(test_vector_vars),
                                                            " ".join(output_vars)))
                    failed += 1
                    var_failed = True
            if not var_failed:
                passed += 1

        if len(error_message) != 0:
            # TODO: Improve print look
            error_message.insert(0, "{} | {}".format(test_vector_data.split(NEWLINE)[0],
                                                       test_vector_data.split(NEWLINE)[0]))
            error_message.insert(0, "Expected\t|Actual Data")

            # Print errors
            for line in error_message:
                print(line)

        return passed, failed, error_message



    def _parse_output_tty_table(self, output):
        str_output = output.stdout.decode("utf-8")
        total_tests = re.search("Running (\d+) vectors", str_output).group(1)
        passed = re.search("Passed: (\d+)", str_output).group(1)
        failed = re.search("Failed: (\d+)", str_output).group(1)

        return str_output, total_tests, passed, failed

    def _get_test_vector_path(self):
        return os.path.join("TestVectors",
                            self.project_name,
                            "test_vector_{}.txt".format(self.circut_name))

    def run(self):
        # output = subprocess.run(["java",
        #                          "-jar",
        #                          type(self).LOGISIM_PATH,
        #                          self.circ_path,
        #                          "-test",
        #                          self.circut_name,
        #                          self._get_test_vector_path(),
        #                          ], stdout=subprocess.PIPE)
        output = subprocess.run(["java",
                                 "-jar",
                                 type(self).LOGISIM_PATH,
                                 self.circ_path,
                                 "-tty",
                                 "table",
                                 "-circuit",
                                 self.circut_name,
                                 ], stdout=subprocess.PIPE)
        return self._validate_output_tty_table(output)

class ProjectTestsRunner(object):
    def __init__(self, circ_path, project_name, circuts_names):
        self.circ_path = circ_path
        self.project_name = project_name
        self.circuts_names = circuts_names

    def run(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Copying file to temp directory in order to prevent any way from logisim to change the file
            shutil.copy2(self.circ_path, f.name)
            temporary_circ_path = f.name

            # Run all test vectors in project
            for circut_name in self.circuts_names:
                circut_test_runner = CircutTestVectorRunner(temporary_circ_path, self.project_name, circut_name)
                circut_test_runner.run()

        print("\nAll Tests have passed!")
