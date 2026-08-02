import abc
import contextlib
import io
import pathlib
import random
import re
import tempfile
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


class TestMain(CliTestCase):
    function_to_test = staticmethod(main)


@forbid("pathlib.Path.replace")
class TestMainWithoutIO(TestMain):

    def test_test_io_protection(self):
        path = pathlib.Path("/dev/null")
        self.assertRaisesRegex(RuntimeError, "/dev/null", path.replace,
                               "anything")

    # Patch basicConfig to keep test console clean.
    @unittest.mock.patch("logging.basicConfig")
    def test_template_compile_error(self, unused_patch):
        invalid_template = "%v"
        with self.assertLogs(level="ERROR") as log_ctx:
            status = self.function_to_test([invalid_template, "/dev/null"])
        self.assertGreater(status, 0)
        self.assertTrue(
            any(invalid_template in message for message in log_ctx.output))

    def test_with_nono(self):
        test_output = self._capture_output(["--nono", "sub/%d", "test"])
        self.assertEqual(test_output.splitlines(),
                         ["rename: 'test' -> 'sub/1'"])


class TestMainWithTmpDir(TestMain):

    def setUp(self):
        # pylint: disable-next=consider-using-with
        self._tmpdir_obj = tempfile.TemporaryDirectory(prefix=f"{self.id()}.")
        self.tmpdir = pathlib.Path(self._tmpdir_obj.name)

    def tearDown(self):
        self._tmpdir_obj.cleanup()

    def test_move_default_sort(self):
        dir0 = self.tmpdir / "dir0"
        dir1 = self.tmpdir / "dir1"
        dir0.mkdir()
        dir1.mkdir()
        n_files = 300
        paths_to_rename = set()
        while len(paths_to_rename) < n_files:
            filename = format(random.randrange(0, 0x8000))
            file_path = dir0 / filename
            file_path.write_text(
                f"I was {file_path.relative_to(self.tmpdir)}\n")
            paths_to_rename.add(str(file_path))
        tmpl = str(dir1 / "%03d-%f")
        status = self.function_to_test([tmpl, *paths_to_rename])
        self.assertEqual(status, 0)
        moved_files = sorted(dir1.iterdir())
        self.assertEqual(len(moved_files), n_files, "files in == files out")
        self.assertTrue(moved_files[0].match("001-*"))
        self.assertTrue(moved_files[-1].match(f"{n_files:03d}-*"))
        original_numbers = [
            int(re.search(r"\d+$", path.read_text())[0])
            for path in moved_files
        ]
        self.assertTrue(
            all(a <= b
                for a, b in zip(original_numbers, original_numbers[1:])),
            "files renamed in sorted order",
        )


if __name__ == "__main__":
    unittest.main()
