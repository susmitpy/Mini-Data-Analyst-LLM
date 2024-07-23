from unittest import TestCase
from utils import get_executable_code_from_message

class TestUtils(TestCase):
    def test_get_executable_code_from_message(self):
        code_with_only_ticks = """
        Sure here is the code
        EXECUTE
        ```
        result = 2 + 2
        ```
        Let me know if you need anything else
        """

        self.assertEqual(get_executable_code_from_message(code_with_only_ticks), "result = 2 + 2")

        code_with_python_ticks = """
        Sure here is the code
        EXECUTE
        ```python
        result = 2 + 2
        ```
        Let me know if you need anything else
        """

        self.assertEqual(get_executable_code_from_message(code_with_python_ticks), "result = 2 + 2")

        invalid_message = """
        Sure here is the code
        EXECUTE
        result = 2 + 2
        Let me know if you need anything else
        """

        with self.assertRaises(Exception):
            get_executable_code_from_message(invalid_message)
