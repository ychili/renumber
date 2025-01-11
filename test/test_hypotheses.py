import unittest

from hypothesis import given
from hypothesis import strategies as st

import renumber


class TestMakeTemplate(unittest.TestCase):

    @given(template=st.text(st.characters(blacklist_characters=["%"])))
    def test_no_percent_sign(self, template: str) -> None:
        """Template strings lacking a '%' will always raise ValueError."""
        self.assertRaises(ValueError, renumber.make_template, template)
