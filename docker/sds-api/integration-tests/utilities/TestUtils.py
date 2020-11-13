import json
import os
import unittest

TEST_DATA_BASE_PATH = os.path.join(os.path.dirname(__file__), '../tests/test_data/')

assertions = unittest.TestCase('__init__')


def read_test_data_json(file):
    with open(os.path.join(TEST_DATA_BASE_PATH, file)) as json_file:
        return json.load(json_file)


def assert_400_operation_outcome(response_content, diagnostics):
    operation_outcome = json.loads(response_content)
    assertions.assertEqual(operation_outcome["resourceType"], "OperationOutcome")
    issue = operation_outcome["issue"][0]
    assertions.assertEqual(issue["severity"], "error")
    assertions.assertEqual(issue["code"], "required")
    assertions.assertEqual(issue["diagnostics"], diagnostics)
    coding = issue["details"]["coding"][0]
    assertions.assertEqual(coding["system"], 'https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1')
    assertions.assertEqual(coding["code"], 'BAD_REQUEST')
    assertions.assertEqual(coding["display"], 'Bad request')


def assert_405_operation_outcome(response_content):
    operation_outcome = json.loads(response_content)
    assertions.assertEqual(operation_outcome["resourceType"], "OperationOutcome")
    issue = operation_outcome["issue"][0]
    assertions.assertEqual(issue["severity"], "error")
    assertions.assertEqual(issue["code"], "not-supported")
    assertions.assertEqual(issue["diagnostics"], 'HTTP operation not supported')
    coding = issue["details"]["coding"][0]
    assertions.assertEqual(coding["system"], 'https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1')
    assertions.assertEqual(coding["code"], 'NOT_IMPLEMENTED')
    assertions.assertEqual(coding["display"], 'Not implemented')


def assert_404_operation_outcome(response_content):
    operation_outcome = json.loads(response_content)
    assertions.assertEqual(operation_outcome["resourceType"], "OperationOutcome")
    issue = operation_outcome["issue"][0]
    assertions.assertEqual(issue["severity"], "error")
    assertions.assertEqual(issue["code"], "not-found")
    assertions.assertEqual(issue["diagnostics"], 'HTTP endpoint not found')
    coding = issue["details"]["coding"][0]
    assertions.assertEqual(coding["system"], 'https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1')
    assertions.assertEqual(coding["code"], 'NOT_IMPLEMENTED')
    assertions.assertEqual(coding["display"], 'Not implemented')
