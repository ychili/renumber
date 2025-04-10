#!/usr/bin/python3
#
# renumber.py
#
# Copyright 2021, 2022, 2024, 2025 Dylan Maltby
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.
#
"""Rename file arguments with consecutive numbering scheme."""

import argparse
import contextlib
import enum
import logging
import pathlib
import re
import string
import sys
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Union

__version__ = "0.5.2"

TEMPLATE_DOC = """
    SUMMARY OF TEMPLATE STRING SYNTAX

    TEMPLATE is a character string which contains at least one NUMBER FORMAT
    directive.

    NUMBER FORMATS (at least 1 required):

      %d   decimal
      %x   hexadecimal lower case
      %X   hexadecimal upper case

    The above number format directives also accept a width modifier between
    the percent sign and the directive, like so: %3d. The number will be
    padded with zeroes to this width.

      %a   alphabetic lower case
      %A   alphabetic upper case

    STRING FORMATS (optional):

      %f   substitute old file name: base name is substituted, i.e. no leading
           path components
      %bf  substitute old file name stem: same as %f with file extension
           removed
      %xf  substitute old file name suffix: same as %f, but file extension
           only

    ESCAPE SEQUENCE:

      %%   literal '%'

    All other characters in TEMPLATE will be taken as literal."""


class Template:
    """Store and parse string template."""

    def __init__(self, template, factory=None):
        self.template = template
        if factory is None:
            self.tokens = tuple()
        else:
            self.compile(factory)

    def __repr__(self):
        return f"{type(self).__name__}({self.template!r})"

    def compile(self, factory):
        """Use FormatterFactory object to store tokens in template."""
        self.tokens = tuple(self.tokenize(factory))
        if not any(token.kind == "INTDIREC" for token in self.tokens):
            raise ValueError(
                "template must contain at least 1 integer directive")

    def substitute(self, *args, **kwargs):
        """Return string with substitutions made."""
        return "".join(token.format(*args, **kwargs) for token in self.tokens)

    def tokenize(self, factory):
        """
        Yield instances of Formatter subclasses for each token in template.
        """
        int_types = IntPresentationType.choices()
        name_forms = NameConversionType.choices()
        token_specification = [
            ("STRDIREC", f"%(?P<NAMEFORM>{name_forms})?f"),
            ("INTDIREC", f"%0?(?P<INTWIDTH>[0-9]+)?(?P<INTTYPE>{int_types})"),
            ("LITERALPERCENT", "%%"),
            ("LITERALSTR", "[^%]+")
        ]
        tok_regex = "|".join(f"(?P<{kind}>{pat})"
                             for kind, pat in token_specification)
        for mo in re.finditer(tok_regex, self.template):
            kind = mo.lastgroup
            if kind == "INTDIREC":
                yield factory(kind,
                              int_type=mo.group("INTTYPE"),
                              int_width=mo.group("INTWIDTH"))
            elif kind == "STRDIREC":
                yield factory(kind, name_form=mo.group("NAMEFORM"))
            elif kind == "LITERALPERCENT":
                yield factory(kind, "%")
            elif kind == "LITERALSTR":
                yield factory(kind, mo.group())


class FormatterFactory:
    """Return instances of Formatter subclasses when called.

    mapping is a dictionary that Formatter objects need to interpret args and
    keyword args passed to them by Template.substitute.
    """

    mapping = {
        "int":         {"arg_ind": 0, "kwd": "number"},
        "file_object": {"arg_ind": 1, "kwd": "file"}
    }

    def __init__(self, mapping=None):
        if mapping is not None:
            self.mapping = mapping

    def __repr__(self):
        return f"{type(self).__name__}({self.mapping!r})"

    def __call__(self, kind, *args, **kwargs):
        """
        Sort token into a Formatter subclass, supplying necessary
        parameters.
        """
        if kind.startswith("LITERAL"):
            value = kwargs.get("value") or args[0]
            return NullFormatter(kind, value)
        if kind == "INTDIREC":
            int_type = kwargs.get("int_type") or args[0]
            int_width = kwargs.get("int_width")
            return self._compile_int_type(kind, int_type, int_width)
        if kind == "STRDIREC":
            name_form = kwargs.get("name_form")
            return self._compile_file_type(kind, name_form or "")
        raise ValueError

    def _compile_int_type(self, kind, int_type, int_width):
        """Subfunction of __call__"""
        int_type = IntPresentationType(int_type)
        int_args = self.mapping["int"]
        # Standard integer presentation types that Python format()
        # understands
        if int_type in (IntPresentationType.DEC,
                        IntPresentationType.HEX_LOWER,
                        IntPresentationType.HEX_UPPER):
            if int_width:
                format_spec = f"0{int_width}{int_type.value}"
            else:
                format_spec = int_type.value
            return IntFormatter(kind, format_spec, **int_args)
        # Custom integer presentation types
        if int_type == IntPresentationType.ALF_LOWER:
            return AlphaIntFormatter(kind, func=str, **int_args)
        if int_type == IntPresentationType.ALF_UPPER:
            return AlphaIntFormatter(kind, func=str.upper, **int_args)
        raise ValueError

    def _compile_file_type(self, kind, name_form=""):
        """Subfunction of __call__"""
        file_object = self.mapping["file_object"]
        if name_form == "":
            return AttrFormatter(kind, name="name", **file_object)
        name_form = NameConversionType(name_form)
        if name_form == NameConversionType.STEM:
            return AttrFormatter(kind, name="stem", **file_object)
        if name_form == NameConversionType.SUFFIX:
            return AttrFormatter(kind, name="suffix", **file_object)
        raise ValueError


class Formatter(ABC):

    def __init__(self, kind):
        self.kind = kind

    @abstractmethod
    def format(self, *args, **kwargs):
        pass


class NullFormatter(Formatter):

    def __init__(self, kind, value):
        super().__init__(kind)
        self.value = value

    def format(self, *args, **kwargs):
        return self.value


class ArgFormatter(Formatter):

    def __init__(self, kind, arg_ind, kwd):
        super().__init__(kind)
        self.arg_ind = arg_ind
        self.kwd = kwd

    def retrieve(self, args, kwargs):
        """
        Try retrieving object from keyword arguments first, then from
        positional argument.
        Raises IndexError on failure.
        """
        with contextlib.suppress(KeyError):
            return kwargs[self.kwd]
        return args[self.arg_ind]


class AttrFormatter(ArgFormatter):

    def __init__(self, kind, name, arg_ind, kwd):
        super().__init__(kind, arg_ind, kwd)
        self.name = name

    def format(self, *args, **kwargs):
        return getattr(self.retrieve(args, kwargs), self.name)


class IntFormatter(ArgFormatter):

    def __init__(self, kind, format_spec, arg_ind, kwd):
        super().__init__(kind, arg_ind, kwd)
        self.format_spec = format_spec

    def format(self, *args, **kwargs):
        number = self.retrieve(args, kwargs)
        return f"{number:{self.format_spec}}"


class AlphaIntFormatter(ArgFormatter):

    def __init__(self, kind, func, arg_ind, kwd):
        super().__init__(kind, arg_ind, kwd)
        self.func = func

    def format(self, *args, **kwargs):
        number = self.retrieve(args, kwargs)
        return self.func(itoa(number - 1))


class REChoiceEnum(enum.Enum):

    @classmethod
    def choices(cls) -> str:
        """String repr of enum values"""
        return "|".join(member.value for member in cls)


class IntPresentationType(REChoiceEnum):
    DEC = "d"
    HEX_LOWER = "x"
    HEX_UPPER = "X"
    ALF_LOWER = "a"
    ALF_UPPER = "A"


class NameConversionType(REChoiceEnum):
    STEM = "b"
    SUFFIX = "x"


class Verbosity(enum.IntEnum):
    QUIET = 0
    VERBOSE = 1


class ManualAction(argparse.Action):
    """Like argparse._HelpAction, print usage manual and exit."""

    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_usage()
        print(TEMPLATE_DOC)
        parser.exit()


def make_template(
    template: str,
    factory: Optional[FormatterFactory] = None
    ) -> Template:
    """Return the default template.

    >>> tmpl = make_template("fore_%d")
    >>> tmpl.substitute(number=101)
    'fore_101'
    >>> tmpl = make_template("newname_%d%xf")
    >>> tmpl.substitute(number=0, file=pathlib.Path("oldname.jpg"))
    'newname_0.jpg'

    Raises ValueError for a bad template string.
    """
    if factory is None:
        factory = FormatterFactory()
    tmpl = Template(template)
    tmpl.compile(factory)
    return tmpl


def itoa(num: int) -> str:
    """Convert integer to base-26 alphabetic string.

    >>> itoa(0)
    'a'
    >>> itoa(25)
    'z'
    >>> itoa(26)
    'aa'
    """
    convert_string = string.ascii_lowercase
    base = len(convert_string)
    if num < base:
        return convert_string[num]
    return itoa(num // base - 1) + convert_string[num % base]


def atoi(s: str) -> Union[int, str]:
    """Also known as `try_int`"""
    try:
        return int(s)
    except ValueError:
        return s


def alphanum_key(s: str) -> List[Union[int, str]]:
    """Turn a string into a list of string and number chunks.

    >>> alphanum_key("z23a")
    ['z', 23, 'a']
    """
    return [atoi(c) for c in re.split("([0-9]+)", s)]


def parse_cla(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="will rename files using consecutive numbering scheme "
        "in sorted order")
    parser.add_argument(
        "-m", "--man", action=ManualAction,
        help="manual: show help message for template formatting and exit")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="verbose: print names of files successfully renamed")
    parser.add_argument(
        "-n", "--nono", action="store_true",
        help="no action: print names of files to be renamed, but don't "
             "rename")
    parser.add_argument(
        "-f", "--force", action="store_true",
        help="over write: allow existing files to be over-written")
    parser.add_argument(
        "-c", "--caseful", action="store_true",
        help="caseful sort: consider letter case when sorting "
             "(default is caseless sort)")
    parser.add_argument(
        "-l", "--lexicographic", action="store_true",
        help="lexicographic sort: sort names on ASCII order")
    parser.add_argument(
        "-r", "--reverse", action="store_true",
        help="reverse sort: number in descending sorted order")
    parser.add_argument(
        "-s", "--start", type=int, default=1, metavar="num",
        help="start number: start numbering with num (default %(default)s)")
    parser.add_argument(
        "-U", "--no-sort", action="store_true",
        help="don't sort: number files in the order given")
    parser.add_argument(
        "-V", "--version", action="version",
        version=f"%(prog)s {__version__}")
    parser.add_argument(
        "template",
        help="template for new filenames. Use --man option for description "
             "of formatting directives.")
    parser.add_argument(
        "files", nargs="+",
        help="files to renumber")
    return parser.parse_args(args)


def main():
    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s")
    args = parse_cla()
    try:
        tmpl = make_template(args.template)
    except ValueError as err:
        logging.error("unable to compile template '%s': %s",
                      args.template,
                      err.args[0])
        return 1

    if args.no_sort:
        files = args.files
    else:
        sfunc = str if args.caseful else str.casefold
        kfunc = str if args.lexicographic else alphanum_key
        files = sorted(args.files,
                       key=lambda s: kfunc(sfunc(s)),
                       reverse=args.reverse)

    for number, file in enumerate(files, start=args.start):
        old_path = pathlib.Path(file)
        new_name = tmpl.substitute(number=number, file=old_path)
        new_path = old_path.with_name(new_name)
        if args.nono:
            print(f"rename: '{old_path}' -> '{new_path}'")
            continue
        if not args.force and new_path.exists():
            if args.verbose >= Verbosity.VERBOSE:
                print(old_path, "->", "file already exists!")
            continue
        try:
            old_path.replace(new_name)
        except OSError as err:
            logging.error("%s", err)
            continue
        if args.verbose >= Verbosity.VERBOSE:
            print(old_path, "->", new_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
