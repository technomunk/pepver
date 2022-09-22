"""
PEP-440 version parsing, interpretation and manipulation.

https://peps.python.org/pep-0440
"""
__version__ = "1.0.0rc2"

import re
from copy import deepcopy
from enum import Enum
from itertools import zip_longest
from typing import Any, ClassVar, List, Literal, Optional, Tuple, Union

VERSION_SUBPATTERNS = {
    "epoch": r"([0-9]+!)?",
    "release": r"[0-9]+(\.[0-9]+)*",
    "pre": r"([-_\.]?(a|b|rc|alpha|beta|c|pre|preview)[-_\.]?[0-9]*)?",
    "post": r"((-[0-9]+)|([-_\.]?(post|r|rev)[-_\.]?[0-9]*))?",
    "dev": r"([-_\.]?dev[-_\.]?[0-9]*)?",
    "local": r"(\+[a-z0-9]+([-_\.][a-z0-9]+)*)?",
}

VERSION_PATTERN = r"\s*v?" + r"".join(VERSION_SUBPATTERNS.values()) + r"\s*"
VERSION_PATTERN_WITH_GROUPS = (
    r"\s*v?"
    + r"".join(rf"(?P<{group}>{pattern})" for group, pattern in VERSION_SUBPATTERNS.items())
    + r"\s*"
)

ReleasePart = Literal["major", "minor", "micro"]
Pre = Tuple[Literal["a", "b", "rc"], int]
RELEASE_ORDER: List[ReleasePart] = ["major", "minor", "micro"]


class VersionPart(Enum):
    """Proper identifiers of version parts. Used primarily for type safety."""

    EPOCH = "epoch"
    MAJOR = "major"
    MINOR = "minor"
    MICRO = "micro"
    PRE = "pre"
    POST = "post"
    DEV = "dev"


class Version:
    """A single fixed version of something. Versions can be compared and updated."""

    PATTERN: ClassVar = re.compile(VERSION_PATTERN_WITH_GROUPS, re.IGNORECASE)
    FIELDS: ClassVar = ["epoch", "release", "pre", "post", "dev", "local"]
    ORDER: ClassVar = ["epoch", "major", "minor", "micro", "release", "pre", "post", "dev", "local"]

    epoch: Optional[int]
    release: Tuple[int, ...]
    pre: Optional[Pre]
    post: Optional[int]
    dev: Optional[int]
    local: Optional[str]

    @classmethod
    def parse(cls, string: str):
        """
        Attempt to parse provided string as a PEP-440 compatible version.
        The parsing accepts all valid variations allowed by the official specification.

        Example versions:
        v1.0.0
        v1.0.0pre
        1.2.3.4.5.dev2+1.2
        11-12
        """
        match = cls.PATTERN.fullmatch(string)
        if match is None:
            raise ValueError(f"'{string}' does not look like a PEP 440 version")
        local = match.group("local")
        return cls(
            epoch=_int_or_none(match.group("epoch")),
            release=_parse_release(match.group("release")),
            pre=_parse_pre(match.group("pre")),
            post=_parse_post(match.group("post")),
            dev=_int_or_none(match.group("dev")),
            local=local[1:] if local else None,
        )

    def public(self) -> str:
        """Get the public part of this version's"""
        # Using a .join method is one of the faster and more memory
        # efficient ways of building strings and we utilize it to full effect.
        result: List[Any] = []
        if self.epoch is not None:
            result.append(self.epoch)
            result.append("!")
        result.extend(self.release)
        if self.pre is not None:
            result.append(",".join(str(part) for part in self.pre))
        if self.post is not None:
            result.append(".post")
            result.append(self.post)
        if self.dev is not None:
            result.append(".dev")
            result.append(self.dev)
        return "".join(str(part) for part in result)

    def is_final(self) -> bool:
        """Check whether this version is final (only contains release and maybe epoch)."""
        return all(getattr(self, field) is None for field in ["pre", "post", "dev", "local"])

    def make_final(self) -> "Version":
        """Drop the non-final segments of this version."""
        return type(self)(epoch=self.epoch, release=self.release)

    def update(self, part: VersionPart, change: int = 1) -> "Version":
        """
        Update a particular part of this version and get the result.

        By default increments the given part of the version by 1, clearing any parts that come
        after the updated. If a particular part of the version did not exist before it is assumed 0.

        str(Version.parse("1.2rc3.dev4").update(VersionPart.PRE)) == "1.2rc4"
        str(Version.parse("1.2").update(VersionPart.MICRO)) == "1.2.1"
        str(Version.parse("1.2.3").update(VersionPart.MINOR, -1)) == "1.1"
        """
        version = deepcopy(self)

        clear = False
        for field in VersionPart:
            if field == part:
                if field == VersionPart.PRE:
                    prefix, value = getattr(version, field.value, ("a", 0))
                    value = prefix, value + change
                else:
                    value = getattr(version, field.value, 0) + change
                setattr(version, field.value, value)
                clear = True
                continue

            if clear:
                setattr(version, field.value, None)

        return version

    def update_release(
        self,
        idx: Union[int, ReleasePart],
        change: int = 1,
    ) -> "Version":
        """
        Update a particular part of the release.
        Behaves similarly to update() except can take the index of a particular release part.

        str(Version.parse("0.1.2.3.4").update_release(3)) == "0.1.2.4"
        str(Version.parse("1.2.3").update_release(0, -1)) == "0"
        str(Version.parse("1.2.3.4.5.6").update_release(-1)) == "1.2.3.4.5.7"
        """
        if isinstance(idx, str):
            idx = RELEASE_ORDER.index(idx)

        if len(self.release) < idx:
            release = (
                *tuple(part for part, _ in zip_longest(self.release, range(idx), fillvalue=0)),
                change,
            )
        else:
            release = *self.release[:idx], self.release[idx] + change
        return type(self)(epoch=self.epoch, release=release)

    @property
    def major(self) -> int:
        """Major (first) segment of the release part."""
        return self.release[0]

    @major.setter
    def major(self, value: int) -> None:
        self.release = value, *self.release[1:]

    @property
    def minor(self) -> Optional[int]:
        """Minor (second) segment of the release part."""
        if len(self.release) < 2:
            return None
        return self.release[1]

    @minor.setter
    def minor(self, value: Optional[int]) -> None:
        if value is None:
            self.release = (self.release[0],)
            return
        self.release = self.release[0], value, *self.release[2:]

    @property
    def micro(self) -> Optional[int]:
        """Micro (third) segment of the release part. In SemVer known as 'patch'"""
        if len(self.release) < 3:
            return None
        return self.release[2]

    @micro.setter
    def micro(self, value: Optional[int]) -> None:
        if value is None:
            self.release = self.release[:2]
            return
        if len(self.release) < 2:
            raise RuntimeError("Setting micro version requires minor version to be present")
        self.release = *self.release[:2], value, *self.release[3:]

    def different_at(self, other: "Version") -> Optional[VersionPart]:
        """
        Find the biggest part (segment) that is different between 2 versions.
        Returns None if the versions are the same.
        """
        for part in VersionPart:
            if getattr(self, part.value) != getattr(other, part.value):
                return part
        return None

    def __init__(
        self,
        release: Union[Tuple[int, ...], int],
        pre: Optional[Pre] = None,
        post: Optional[int] = None,
        dev: Optional[int] = None,
        *,
        epoch: Optional[int] = None,
        local: Optional[str] = None,
    ) -> None:
        self.epoch = epoch
        if isinstance(release, int):
            self.release = (release,)
        else:
            self.release = release
        self.pre = pre
        self.post = post
        self.dev = dev
        self.local = local

    def __str__(self) -> str:
        result = self.public()
        if self.local is not None:
            result += f"+{self.local}"
        return result

    def __repr__(self) -> str:
        args = []
        for field in self.FIELDS:
            value = getattr(self, field)
            if isinstance(value, str):
                value = f"'{value}'" if value else None
            if value is not None:
                args.append(f"{field}={value}")

        return f'Value({", ".join(args)})'

    def _less(self, other: "Version", *, if_equal: bool) -> bool:
        for field in self.FIELDS:
            diff = _lt_or_none(getattr(self, field), getattr(other, field))
            if diff is not None:
                return diff

        return if_equal

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._less(other, if_equal=False)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._less(other, if_equal=True)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        for field in self.FIELDS:
            if getattr(self, field) != getattr(other, field):
                return False

        return True

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return not self._less(other, if_equal=True)  # note that if equal is inverted

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return not self._less(other, if_equal=False)  # note that if equal is inverted


def _int_or_none(string: Optional[str]) -> Optional[int]:
    """Map strings to integers and falsy strings to Nones"""
    if not string:
        return None
    return int(re.sub(r"[^0-9]", "", string) or 0)


def _parse_release(string: str) -> Tuple[int, ...]:
    parts = string.split(".")
    return tuple(int(part) for part in parts)


def _parse_pre(string: Optional[str]) -> Optional[Pre]:
    if not string:
        return None
    prefix: Literal["a", "b", "rc"]
    string = string.strip(".-_").lower()
    if string.startswith(("a", "alpha")):
        prefix = "a"
    elif string.startswith(("b", "beta")):
        prefix = "b"
    elif string.startswith(("rc", "c", "pre", "preview")):
        prefix = "rc"
    else:
        raise ValueError(f"'{string}' is not a valid pre-release segment")

    numeric = re.sub(r"[^0-9]", "", string)
    return prefix, int(numeric or 0)


def _parse_post(string: Optional[str]) -> Optional[int]:
    if not string:
        return None
    if string.startswith("-") and string[1:].isnumeric():
        return int(string[1:])
    return int(string.strip("._-postrev") or 0)


def _lt_or_none(left: Optional[Any], right: Optional[Any]) -> Optional[bool]:
    """None is always considered smaller than something. If the items are equal returns None."""
    if left is None:
        if right is None:
            return None
        return True
    if right is None:
        return False
    if left == right:
        return None
    return left < right
