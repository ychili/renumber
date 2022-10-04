import doctest
import unittest

import renumber


def load_tests(unused_loader, tests, unused_ignore):
    tests.addTests(doctest.DocTestSuite(renumber))
    return tests


if __name__ == "__main__":
    unittest.main()
