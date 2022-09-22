# pepver

[![Python versions](https://img.shields.io/pypi/pyversions/pepver.svg)](https://pypi.org/project/pepver)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Unit tests](https://github.com/technomunk/pepver/actions/workflows/test.yml/badge.svg)](https://github.com/technomunk/pepver/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

PEP-440 version parsing, interpretation and manipulation.

```py
>>> from pepver import Version
>>> version = Version.parse("0!1.2.3.4a5.post6.dev7+8.9")
>>> version.epoch
0
>>> version.release
(1, 2, 3, 4)
>>> version.major
1
>>> version.minor
2
>>> version.micro
3
>>> version.pre
('a', 5)
>>> version.post
6
>>> version.dev
7
>>> version.local
'8.9'
```

## Usage

The main star of the library is the `Version` class, which encompasses the semantics of a version string.
It can be instantiated directly or be parsed from a string:
```py
>>> from pepver import Version
>>> Version(1, 2, 3, 4)
Value(release=(1,), pre=2, post=3, dev=4)
>>> Version((0, 1, 2, 3), post=11, epoch=1)
Value(epoch=1, release=(0, 1, 2, 3), post=11)
>>> Version.parse("11.2")
Value(release=(11, 2))
```

Versions can be updated to suit one's needs:
```py
>>> from pepver import Version
>>> version = Version.parse("0!1.2.3.4a5.post6.dev7+8.9")
>>> version.update("minor")
Value(epoch=0, release=(1, 3))
>>> version.update("post", -2)
Value(epoch=0, release=(1, 2, 3, 4), pre=('a', 5), post=4)
>>> version.update("release")
Value(epoch=0, release=(1, 2, 3, 5))
>>> version.update("release").is_final()
True
```

Versions correctly convert into strings. Note that the conversion is "normalized" ie
standard representation that is the same for the same version:

```py
>>> from pepver import Version
>>> str(Version.parse("010.12-11"))
'10.12.post11'
>>> str(Version.parse("1.2.3preview11dev"))
'1.2.3rc11.dev0'
```
