import xml.etree.ElementTree as ET
from typing import List, Dict, Any


class JUnitReporter:
    """
    Exports TerminalBench evaluation run records into standard JUnit XML format for CI/CD runners.
    """

    def __init__(self, suite_name: str = "TerminalBench"):
        self.suite_name = suite_name

    def generate_xml(self, records: List[Dict[str, Any]]) -> str:
        total = len(records)
        failures = sum(1 for r in records if not r.get("passed", False))

        testsuite = ET.Element("testsuite", name=self.suite_name, tests=str(total), failures=str(failures))

        for r in records:
            task_id = r.get("task_id", "task_unknown")
            duration = str(r.get("latency_seconds", 0.0))
            testcase = ET.SubElement(testsuite, "testcase", classname="TerminalBenchTask", name=task_id, time=duration)

            if not r.get("passed", False):
                failure = ET.SubElement(testcase, "failure", message="Task verification assertion failed")
                failure.text = r.get("error_trace", "Oracle state did not match expected directory tree or return code.")

        return ET.tostring(testsuite, encoding="unicode", xml_declaration=True)
