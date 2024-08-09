import os
from request.cpm import should_use_cpm, CPM_FILTER_IDENTIFIER
import pytest
from unittest import mock


@pytest.mark.parametrize(
    ["cpm_filter", "result"], [(CPM_FILTER_IDENTIFIER, True), ("anything else", False)]
)
def test_is_cpm_query_with_inputs(cpm_filter, result):
    mocked_handler = mock.Mock()
    mocked_handler.get_query_argument.return_value = result
    assert should_use_cpm(mocked_handler) is result


@pytest.mark.parametrize(
    ["cpm_filter", "result"], [(CPM_FILTER_IDENTIFIER, True), ("anything else", False)]
)
def test_is_cpm_query_with_inputs_and_env_var_off(cpm_filter, result):
    mocked_handler = mock.Mock()
    mocked_handler.get_query_argument.return_value = result

    with mock.patch.dict(os.environ, {"USE_CPM": "0"}):
        assert should_use_cpm(mocked_handler) is result


@pytest.mark.parametrize(
    ["cpm_filter", "result"], [(CPM_FILTER_IDENTIFIER, True), ("anything else", False)]
)
def test_is_cpm_query_with_inputs_and_env_var_on(cpm_filter, result):
    mocked_handler = mock.Mock()
    mocked_handler.get_query_argument.return_value = result

    with mock.patch.dict(os.environ, {"USE_CPM": "1"}):
        assert should_use_cpm(mocked_handler) is True
