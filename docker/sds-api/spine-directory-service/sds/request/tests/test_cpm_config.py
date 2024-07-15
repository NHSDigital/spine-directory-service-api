import os
from request.cpm_config import is_cpm_query, CPM_FILTER_IDENTIFIER
import pytest
from unittest import mock

@pytest.mark.parametrize(["cpm_filter","result"], [(CPM_FILTER_IDENTIFIER, True), ("anything else", False)])
def test_is_cpm_query_with_inputs(cpm_filter, result):
    assert is_cpm_query(cpm_filter) is result


@pytest.mark.parametrize(["cpm_filter","result"], [(CPM_FILTER_IDENTIFIER, True), ("anything else", False)])
def test_is_cpm_query_with_inputs_and_env_var_off(cpm_filter, result):
    with mock.patch.dict(os.environ, {"USE_CPM": "0"}):
        assert is_cpm_query(cpm_filter) is result

@pytest.mark.parametrize("cpm_filter", [CPM_FILTER_IDENTIFIER, "anything else"])
def test_is_cpm_query_with_inputs_and_env_var_on(cpm_filter):
    with mock.patch.dict(os.environ, {"USE_CPM": "1"}):
        assert is_cpm_query(cpm_filter) is True
