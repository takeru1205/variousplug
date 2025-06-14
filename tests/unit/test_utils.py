"""
Unit tests for VariousPlug utility functions.
"""
from io import StringIO
from unittest.mock import patch

import pytest

from variousplug.utils import ExecutionResult, print_error, print_info, print_success, print_warning


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_execution_result_success(self):
        """Test ExecutionResult for successful execution."""
        result = ExecutionResult(
            success=True,
            output="Command executed successfully",
            error="",
            return_code=0
        )

        assert result.success is True
        assert result.output == "Command executed successfully"
        assert result.error == ""
        assert result.return_code == 0

    def test_execution_result_failure(self):
        """Test ExecutionResult for failed execution."""
        result = ExecutionResult(
            success=False,
            output="",
            error="Command failed",
            return_code=1
        )

        assert result.success is False
        assert result.output == ""
        assert result.error == "Command failed"
        assert result.return_code == 1

    def test_execution_result_defaults(self):
        """Test ExecutionResult with default values."""
        result = ExecutionResult(success=True)

        assert result.success is True
        assert result.output == ""
        assert result.error == ""
        assert result.return_code == 0

    def test_execution_result_with_output_only(self):
        """Test ExecutionResult with only output."""
        result = ExecutionResult(
            success=True,
            output="Some output"
        )

        assert result.success is True
        assert result.output == "Some output"
        assert result.error == ""
        assert result.return_code == 0

    def test_execution_result_with_error_only(self):
        """Test ExecutionResult with only error."""
        result = ExecutionResult(
            success=False,
            error="Some error"
        )

        assert result.success is False
        assert result.output == ""
        assert result.error == "Some error"
        assert result.return_code == 0


class TestPrintFunctions:
    """Test utility print functions."""

    def test_print_info(self):
        """Test print_info function."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info("This is an info message")
            output = mock_stdout.getvalue()

            assert "ℹ️" in output
            assert "This is an info message" in output

    def test_print_error(self):
        """Test print_error function."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_error("This is an error message")
            output = mock_stderr.getvalue()

            assert "❌" in output
            assert "This is an error message" in output

    def test_print_warning(self):
        """Test print_warning function."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_warning("This is a warning message")
            output = mock_stdout.getvalue()

            assert "⚠️" in output
            assert "This is a warning message" in output

    def test_print_success(self):
        """Test print_success function."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_success("This is a success message")
            output = mock_stdout.getvalue()

            assert "✅" in output
            assert "This is a success message" in output

    def test_print_functions_with_empty_string(self):
        """Test print functions with empty strings."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info("")
            output = mock_stdout.getvalue()
            assert "ℹ️" in output

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_error("")
            output = mock_stderr.getvalue()
            assert "❌" in output

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_warning("")
            output = mock_stdout.getvalue()
            assert "⚠️" in output

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_success("")
            output = mock_stdout.getvalue()
            assert "✅" in output

    def test_print_functions_with_multiline(self):
        """Test print functions with multiline messages."""
        multiline_message = "Line 1\nLine 2\nLine 3"

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info(multiline_message)
            output = mock_stdout.getvalue()

            assert "ℹ️" in output
            assert "Line 1" in output
            assert "Line 2" in output
            assert "Line 3" in output

    def test_print_functions_with_special_characters(self):
        """Test print functions with special characters."""
        special_message = "Special chars: àáâãäå ñ ç β § ♠ ♣ ♥ ♦"

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info(special_message)
            output = mock_stdout.getvalue()

            assert "ℹ️" in output
            assert special_message in output

    def test_print_functions_output_destinations(self):
        """Test that print functions output to correct streams."""
        message = "test message"

        # Info, warning, success should go to stdout
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("sys.stderr", new_callable=StringIO) as mock_stderr:

            print_info(message)
            print_warning(message)
            print_success(message)

            stdout_output = mock_stdout.getvalue()
            stderr_output = mock_stderr.getvalue()

            assert message in stdout_output
            assert message not in stderr_output

        # Error should go to stderr
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("sys.stderr", new_callable=StringIO) as mock_stderr:

            print_error(message)

            stdout_output = mock_stdout.getvalue()
            stderr_output = mock_stderr.getvalue()

            assert message not in stdout_output
            assert message in stderr_output

    def test_print_functions_with_long_messages(self):
        """Test print functions with very long messages."""
        long_message = "A" * 1000  # 1000 character message

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info(long_message)
            output = mock_stdout.getvalue()

            assert "ℹ️" in output
            assert long_message in output

    def test_print_functions_unicode_emojis(self):
        """Test that emoji characters are properly handled."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info("Test message")
            output = mock_stdout.getvalue()

            # Check that the emoji is present (might be different based on system)
            assert any(char in output for char in ["ℹ️", "ℹ", "i"])

    def test_execution_result_truthiness(self):
        """Test ExecutionResult truthiness based on success."""
        success_result = ExecutionResult(success=True)
        failure_result = ExecutionResult(success=False)

        # Test boolean evaluation
        assert bool(success_result) is True
        assert bool(failure_result) is False

        # Test in if statements
        if success_result:
            success_check = True
        else:
            success_check = False
        assert success_check is True

        if failure_result:
            failure_check = True
        else:
            failure_check = False
        assert failure_check is False

    def test_execution_result_string_representation(self):
        """Test ExecutionResult string representation."""
        result = ExecutionResult(
            success=True,
            output="Test output",
            error="Test error",
            return_code=0
        )

        str_repr = str(result)

        # Should contain key information
        assert "ExecutionResult" in str_repr
        assert "success=True" in str_repr
        assert "output='Test output'" in str_repr
        assert "error='Test error'" in str_repr
        assert "return_code=0" in str_repr

    def test_execution_result_repr(self):
        """Test ExecutionResult repr."""
        result = ExecutionResult(success=False, error="Failed")

        repr_str = repr(result)

        # Should be a valid representation
        assert "ExecutionResult" in repr_str
        assert "success=False" in repr_str
        assert "error='Failed'" in repr_str

    def test_execution_result_equality(self):
        """Test ExecutionResult equality comparison."""
        result1 = ExecutionResult(success=True, output="test")
        result2 = ExecutionResult(success=True, output="test")
        result3 = ExecutionResult(success=False, output="test")

        assert result1 == result2
        assert result1 != result3
        assert result2 != result3

    def test_execution_result_with_none_values(self):
        """Test ExecutionResult with None values."""
        result = ExecutionResult(
            success=True,
            output=None,
            error=None,
            return_code=None
        )

        assert result.success is True
        assert result.output is None
        assert result.error is None
        assert result.return_code is None

    def test_print_functions_error_handling(self):
        """Test print functions handle errors gracefully."""
        # Test with broken stdout/stderr
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.write.side_effect = Exception("Write failed")

            # Should not raise exception
            try:
                print_info("test")
            except Exception:
                pytest.fail("print_info should handle stdout errors gracefully")

        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = Exception("Write failed")

            # Should not raise exception
            try:
                print_error("test")
            except Exception:
                pytest.fail("print_error should handle stderr errors gracefully")
