import os
import shutil
import subprocess
import re
import tempfile

from infra.Exceptions import InfraException

NEWLINE = "\n"
TOTAL_FAILURES = 0

def print_table(rows):
    """print_table(rows)
    Prints out a table using the data in `rows`, which is assumed to be a
    sequence of sequences with the 0th element being the header.
    """

    # - figure out column widths
    widths = [ len(max(columns, key=len)) for columns in zip(*rows) ]

    # - print the header
    header, data = rows[0], rows[1:]
    print(
        ' | '.join( format(title, "%ds" % width) for width, title in zip(widths, header) )
        )

    # - print the separator
    print( '-+-'.join( '-' * width for width in widths ) )

    # - print the data
    for row in data:
        print(
            " | ".join( format(cdata, "%ds" % width) for width, cdata in zip(widths, row) )
            )


class CircutTestVectorRunner(object):
    LOGISIM_PATH = "Dependencies/logisim-2.7.2-cs3410-20140215.jar"

    def __init__(self, circ_path, project_name, circuit_name):
        self.circ_path = circ_path
        self.project_name = project_name
        self.circuit_name = circuit_name

    def generate_errors_report(self, error_lines):

        with open(self._get_test_vector_path()) as f:
            test_vector_data = f.read()
        test_vector_data = NEWLINE.join([x for x in test_vector_data.split("\n") if
                                         not x.startswith("#") and x != ''])

        errors_report = []
        var_names = [re.sub("[\(\[].*?[\)\]]", "", x) for x in test_vector_data.split(NEWLINE)[0].split()]
        a = ["Expected: " + x for x in var_names]
        b = ["Actual: " + x for x in var_names]
        errors_report.append(a + b)
        for error_line in error_lines:
            line_number, error_message = error_line

            expected_vars = test_vector_data.split(NEWLINE)[int(line_number)].split()
            actual_vars = test_vector_data.split(NEWLINE)[int(line_number)].split()
            # Find actual data which does not match expected data
            bla = re.search("(\w) = (\w+) \(expected (\w+)\)", error_message.strip())
            variable_name = bla.group(1)
            actual_var = bla.group(2)
            expected_var = bla.group(3)
            actual_vars[var_names.index(variable_name)] = actual_var
            errors_report.append(expected_vars + actual_vars)
        return errors_report

    def _validate_output_test_vector(self, output):
        str_output, total_tests, passed, failed, error_lines = self._parse_output_test_vector(output)

        errors_report = self.generate_errors_report(error_lines)

        if int(failed) != len(error_lines):
            raise InfraException("Expected to have {} error but had {} error lines".format(
                int(failed),
                error_lines
            ))

        if int(failed) > 0:
            print("\n{} - {} failures".format(int(failed), self.circuit_name))
            print_table(errors_report)
        else:
            print("{} - Passed".format(self.circuit_name))

        return int(failed)

    def _parse_output_test_vector(self, output):
        # Very hacky function to parse logisims output
        str_output = output.stdout.decode("utf-8")
        str_err = output.stderr.decode("utf-8")

        if "Error loading test vector" in str_err:
            raise InfraException("Error while loading test vector. Full stderr: {}".format(str_err))

        if "Circuit '{}' not found".format(self.circuit_name) in str_err:
            raise InfraException("Circuit not found at circ file. Full stderr: {}".format(str_err))

        total_tests = re.search("Running (\d+) vectors", str_output).group(1)
        passed = re.search("Passed: (\d+)", str_output).group(1)
        failed = re.search("Failed: (\d+)", str_output).group(1)
        # TODO: Remove this hack!
        global TOTAL_FAILURES
        TOTAL_FAILURES += int(failed)

        error_lines = []

        # Find line number of the error. It appears at the previous line each time
        prev = None
        for i in "".join(str_output.split("\r")).split("\n"):
            if "expected" in i:
                error_lines.append((prev, i))
            stripped_i = i.strip()
            if len(stripped_i) > 0 and stripped_i[-1].isnumeric():
                prev = stripped_i.split(" ")[-1]

        return str_output, total_tests, passed, failed, error_lines

    def _get_test_vector_path(self):
        return os.path.join("TestVectors",
                            self.project_name,
                            "test_vector_{}.txt".format(self.circuit_name))

    def run(self):
        output = subprocess.run(["java",
                                 "-jar",
                                 type(self).LOGISIM_PATH,
                                 self.circ_path,
                                 "-test",
                                 self.circuit_name,
                                 self._get_test_vector_path(),
                                 ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if output.returncode != 0:
            raise InfraException("Error while executing logisim.\nstdout:{}\nstderr:{}".format(
                output.stdout,
                output.stderr
            ))
        return self._validate_output_test_vector(output)

class ProjectTestsRunner(object):
    def __init__(self, circ_path, project_name, circuts_names):
        self.circ_path = circ_path
        self.project_name = project_name
        self.circuits_names = circuts_names
        # TODO: Remove this hack!
        global TOTAL_FAILURES

    def run(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Copying file to temp directory in order to prevent any way from logisim to change the file
            shutil.copy2(self.circ_path, f.name)
            temporary_circ_path = f.name

            # Run all test vectors in project
            for circuit_name in self.circuits_names:
                circuit_test_runner = CircutTestVectorRunner(temporary_circ_path, self.project_name, circuit_name)
                circuit_test_runner.run()

        if 0 != TOTAL_FAILURES:
            print("\nFound {} failures in total".format(TOTAL_FAILURES))
        else:
            print("\nAll tests have passed!")

