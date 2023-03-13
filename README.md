# Description

"renumber" renames the filenames supplied according to the template
provided as the first argument using a consecutive numbering scheme.
By default, filenames are sorted before numbering.

# Requirements

  - Python 3.6+

"renumber" is designed to make use of POSIX shell features.

# Motivation

Maybe you’ve received some files in a directory from someone else,
maybe off the internet.
And their naming scheme sucks, maybe hashes.
So just rename all those files so they are consecutively numbered.
Most "downloader" programs enable you to do this,
but if you missed that step it can be a pain to manually renumber files.
I recommend using in conjunction with [**rename**(1p)][1].

The **Thunar**(1) File Manager for Xfce has a similar capability called
["Bulk Rename"][2] with a convenient graphical interface.
You are however limited on where you can place the number in the new name.
The only requirement of this program’s template string is that
the number has to go somewhere.

[1]: https://metacpan.org/release/File-Rename
[2]: https://docs.xfce.org/xfce/thunar/bulk-renamer/start

# Usage

    renumber set_%3d.jpg *.jpg

This example will rename all files matching `*.jpg` to
set\_001.jpg, set\_002.jpg, set\_003.jpg, etc.
Use the `--help` option to show info about further options.
Use the `--man` option to show info about formatting directives
for the template.

The default sorting method is caseless [natural sort][3],
sometimes called ["version" sort][4] or ["sorting for humans."][5]
This method can be changed or sorting disabled altogether using the options.

[3]: https://en.wikipedia.org/wiki/Natural_sort_order
[4]: https://www.gnu.org/software/coreutils/manual/html_node/Version-sort-overview.html
[5]: https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/

# Copyright

Copyright © 2021, 2022 Dylan Maltby

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.
