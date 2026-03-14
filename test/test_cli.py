import abc
import contextlib
import io
import pathlib
import unittest
import unittest.mock

from renumber import TEMPLATE_DOC, __version__, main, parse_cla


def forbid(target, reason=None):

    def patched(*args, **kwargs):
        msg = f"Forbidden function '{target}' called with: {args}; {kwargs}"
        if reason:
            msg += f": {reason}"
        raise RuntimeError(msg)

    return unittest.mock.patch(target, patched)


class CliTestCase(unittest.TestCase, abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def function_to_test(args=None):
        raise NotImplementedError

    def _capture_output(self, args=None):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            with contextlib.suppress(SystemExit):
                self.function_to_test(args)
        return buf.getvalue()


class TestCommandLine(CliTestCase):
    function_to_test = staticmethod(parse_cla)

    def test_manual_action(self):
        man_output = self._capture_output(["--man"])
        self.assertIn(TEMPLATE_DOC, man_output)

    def test_version_action(self):
        version_output = self._capture_output(["--version"])
        self.assertIn(__version__, version_output)


@forbid("pathlib.Path.replace")
class TestMain(CliTestCase):
    function_to_test = staticmethod(main)

    def test_test_io_protection(self):
        path = pathlib.Path("/dev/null")
        self.assertRaisesRegex(RuntimeError, "/dev/null", path.replace,
                               "anything")

    def test_with_nono(self):
        test_output = self._capture_output(["--nono", "%d", "test"])
        self.assertEqual(test_output.splitlines(), ["rename: 'test' -> '1'"])


if __name__ == "__main__":
    unittest.main()
