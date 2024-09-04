import contextlib
import io
import unittest

from renumber import TEMPLATE_DOC, __version__, parse_cla


class TestCommandLine(unittest.TestCase):

    def _capture_output(self, args=None):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            with contextlib.suppress(SystemExit):
                parse_cla(args)
        return buf.getvalue()

    def test_manual_action(self):
        man_output = self._capture_output(["--man"])
        self.assertIn(TEMPLATE_DOC, man_output)

    def test_version_action(self):
        version_output = self._capture_output(["--version"])
        self.assertIn(__version__, version_output)


if __name__ == "__main__":
    unittest.main()
