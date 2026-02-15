import string
import unittest

from hypothesis import given
from hypothesis import strategies as st

import renumber


class TestMakeTemplate(unittest.TestCase):

    @given(template=st.text(st.characters(blacklist_characters=["%"])))
    def test_no_percent_sign(self, template: str) -> None:
        """Template strings lacking a '%' will always raise ValueError."""
        self.assertRaises(ValueError, renumber.make_template, template)


class TestFuzz(unittest.TestCase):

    @given(st.integers(min_value=0))
    def test_fuzz_itoa(self, num: int) -> None:
        result = renumber.itoa(num)
        self.assertTrue(result)
        self.assertTrue(all(c in string.ascii_lowercase for c in result))

    @given(st.text())
    def test_fuzz_alphanum_key(self, s: str) -> None:
        result = renumber.alphanum_key(s)
        self.assertTrue(result)
        self.assertTrue(callable(result.__lt__),
                        "key functions work by using Less Than")
        for chunk in result:
            if isinstance(chunk, str):
                self.assertIn(chunk, s)
            elif isinstance(chunk, int):
                self.assertGreaterEqual(chunk, 0)
            else:
                raise TypeError(chunk)
