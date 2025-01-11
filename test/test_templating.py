import unittest
from pathlib import Path

from renumber import Template, make_template


class TestCreation(unittest.TestCase):

    def test_simple(self):
        self.assertIsInstance(make_template("%d"), Template)

    def test_no_integer(self):
        for example in ("%", "%%", "%%d", "%f"):
            with self.subTest(example=example):
                self.assertRaises(ValueError, make_template, example)


class TestObjecthood(unittest.TestCase):

    def setUp(self):
        self.tmpl = make_template("fore_%x.jpg")

    def test_tokenization(self):
        self.assertEqual(len(self.tmpl.tokens), 3)

    def test_literal_values(self):
        self.assertEqual(self.tmpl.tokens[0].value, "fore_")
        self.assertEqual(self.tmpl.tokens[2].value, ".jpg")

    def test_directive(self):
        self.assertEqual(self.tmpl.tokens[1].format_spec, "x")


class TestSubstitutionResult(unittest.TestCase):

    def test_decimal(self):
        tmpl = make_template("./file_set_01_img_%3d.jpg")
        self.assertEqual(tmpl.substitute(1), "./file_set_01_img_001.jpg")
        self.assertEqual(tmpl.substitute(1001), "./file_set_01_img_1001.jpg")
        self.assertEqual(tmpl.substitute(0), "./file_set_01_img_000.jpg")
        self.assertEqual(tmpl.substitute(-5), "./file_set_01_img_-05.jpg")

    def test_hexadecimal_lower(self):
        tmpl = make_template("img_%3x.jpg")
        self.assertEqual(tmpl.substitute(1), "img_001.jpg")
        self.assertEqual(tmpl.substitute(12648430), "img_c0ffee.jpg")

    def test_hexadecimal_upper(self):
        tmpl = make_template("img_%X.jpg")
        self.assertEqual(tmpl.substitute(0), "img_0.jpg")
        self.assertEqual(tmpl.substitute(123), "img_7B.jpg")

    def test_alphabetic_lower(self):
        tmpl = make_template("img_%a.jpg")
        self.assertEqual(tmpl.substitute(1), "img_a.jpg")
        self.assertEqual(tmpl.substitute(28), "img_ab.jpg")

    def test_alphabetic_upper(self):
        tmpl = make_template("img_%02A.jpg")
        self.assertEqual(tmpl.substitute(0), "img_Z.jpg")
        self.assertEqual(tmpl.substitute(10), "img_J.jpg")
        self.assertEqual(tmpl.substitute(100), "img_CV.jpg")

    def test_mixed_integers(self):
        tmpl = make_template("%A %2d.txt")
        self.assertEqual(tmpl.substitute(1), "A 01.txt")
        self.assertEqual(tmpl.substitute(15), "O 15.txt")

    def test_escaping(self):
        tmpl = make_template("100%% True - Ep%2d.mp4")
        self.assertEqual(tmpl.substitute(1), "100% True - Ep01.mp4")

    def test_filename(self):
        tmpl = make_template("%d %f")
        self.assertEqual(tmpl.substitute(9, PATH), "9 oldname_xxx.jpg")

    def test_filename_stem(self):
        tmpl = make_template("%bf (%d).jpeg")
        self.assertEqual(tmpl.substitute(2, PATH), "oldname_xxx (2).jpeg")

    def test_filename_partition(self):
        tmpl = make_template("%bf_%3d%xf")
        self.assertEqual(tmpl.substitute(1, PATH), "oldname_xxx_001.jpg")

    def test_filename_suffix(self):
        tmpl = make_template("folder/newname_%d%xf")
        self.assertEqual(tmpl.substitute(1, PATH), "folder/newname_1.jpg")


class TestSubstitutionInvocation(unittest.TestCase):

    def setUp(self):
        self.tmpl = make_template("%03d - %f")

    def test_bad_positional(self):
        self.assertRaises(TypeError, self.tmpl.substitute, PATH, 1)

    def test_good_kwd(self):
        self.assertEqual(self.tmpl.substitute(file=PATH, number=1),
                         "001 - oldname_xxx.jpg")

    def test_bad_kwd(self):
        self.assertRaises(IndexError, self.tmpl.substitute, file=PATH, none=1)

    def test_bad_type(self):
        self.assertRaises(ValueError,
                          self.tmpl.substitute,
                          number=3.14,
                          file=PATH)
        self.assertRaises(AttributeError,
                          self.tmpl.substitute,
                          number=1,
                          file="PATH")


PATH = Path("oldname_xxx.jpg")

if __name__ == "__main__":
    unittest.main()
