import pytest
import os

from unittest import mock

from lib.assessment.rubric_tester import (
    main,
)

accuracy = pytest.mark.skipif("not config.getoption('accuracy')")

@accuracy
@pytest.mark.accuracy_setup
class TestAccuracy:
    def test_accuracy(self):
        assert "OPENAI_API_KEY" in os.environ
        with mock.patch('sys.argv', ['rubric_tester.py', '-a']):
            ret = main()
        assert ret == True
        