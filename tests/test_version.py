from typing import Tuple

import pytest

from pepver import Version, VersionPart


@pytest.mark.parametrize(
    ["string", "expected"],
    [
        ["0", Version(0)],
        ["1", Version(1)],
        ["11", Version(11)],
        ["1.2", Version((1, 2))],
        ["1.2.3", Version((1, 2, 3))],
        ["1.2.3.4", Version((1, 2, 3, 4))],
        ["1.2.3.4.5", Version((1, 2, 3, 4, 5))],
        ["12.34.56.78.9", Version((12, 34, 56, 78, 9))],
        ["2!0", Version(epoch=2, release=0)],
        ["42!0", Version(epoch=42, release=0)],
        ["1.2a1", Version((1, 2), pre=("a", 1))],
        ["1.2b12", Version((1, 2), pre=("b", 12))],
        ["1.2rc420", Version((1, 2), pre=("rc", 420))],
        ["1.2.post1", Version((1, 2), post=1)],
        ["1.2.post42", Version((1, 2), post=42)],
        ["1.2.dev2", Version((1, 2), dev=2)],
        ["1.2.dev42", Version((1, 2), dev=42)],
        ["1.2rc1.post42", Version((1, 2), pre=("rc", 1), post=42)],
        ["1.2.post42.dev12", Version((1, 2), post=42, dev=12)],
        ["1.2a1.dev2", Version((1, 2), pre=("a", 1), dev=2)],
        ["1.2b11.post42.dev12", Version((1, 2), pre=("b", 11), post=42, dev=12)],
        ["1.2+something", Version((1, 2), local="something")],
        [
            "1!2.3.4.5a6.post7.dev8+9",
            Version(epoch=1, release=(2, 3, 4, 5), pre=("a", 6), post=7, dev=8, local="9"),
        ],
    ],
)
def test_parse(string: str, expected: Version) -> None:
    parsed = Version.parse(string)
    print(repr(parsed), str(parsed))
    assert parsed == expected
    assert str(parsed) == string


@pytest.mark.parametrize(
    ["original", "normalized", "value"],
    [
        ["01", "1", Version(1)],
        ["0.02", "0.2", Version((0, 2))],
        ["0.1alpha2", "0.1a2", Version((0, 1), ("a", 2))],
        ["0.1.a2", "0.1a2", Version((0, 1), ("a", 2))],
        ["0.1.beta2", "0.1b2", Version((0, 1), ("b", 2))],
        ["0.1-c2", "0.1rc2", Version((0, 1), ("rc", 2))],
        ["0.1_pre2", "0.1rc2", Version((0, 1), ("rc", 2))],
        ["0.1preview2", "0.1rc2", Version((0, 1), ("rc", 2))],
        ["0.1pre", "0.1rc0", Version((0, 1), ("rc", 0))],
        ["0.1rev1", "0.1.post1", Version((0, 1), post=1)],
        ["0.1-r", "0.1.post0", Version((0, 1), post=0)],
        ["0.1_post", "0.1.post0", Version((0, 1), post=0)],
        ["0.1-11", "0.1.post11", Version((0, 1), post=11)],
        ["0.1.dev", "0.1.dev0", Version((0, 1), dev=0)],
        ["0.1-dev1", "0.1.dev1", Version((0, 1), dev=1)],
        ["0.1_dev2", "0.1.dev2", Version((0, 1), dev=2)],
        ["0.1dev3", "0.1.dev3", Version((0, 1), dev=3)],
    ],
)
def test_normalize(original: str, normalized: str, value: Version) -> None:
    parsed = Version.parse(original)
    assert parsed == value
    assert str(parsed) == normalized


def test_version_order() -> None:
    # versions should be defined in descending order (ie later versions come later)
    versions = [
        Version(0),
        Version(1),
        Version((1, 1)),
        Version((1, 1, 1)),
        Version((1, 1, 1, 1)),
        Version((1, 1, 1, 1, 1)),
        Version((1, 2)),
        Version((1, 2), dev=0),
        Version((1, 2), dev=1),
        Version((1, 2), post=0),
        Version((1, 2), post=0, dev=0),
        Version((1, 2), post=0, dev=1),
        Version((1, 2), post=1),
        Version((1, 2), post=1, dev=0),
        Version((1, 2), pre=("a", 0)),
        Version((1, 2), pre=("a", 1)),
        Version((1, 2), pre=("a", 1), dev=0),
        Version((1, 2), pre=("a", 1), dev=1),
        Version((1, 2), pre=("a", 1), post=0),
        Version((1, 2), pre=("a", 1), post=1),
        Version((1, 2), pre=("a", 1), post=1, dev=0),
        Version((1, 2), pre=("a", 1), post=1, dev=1),
        Version((1, 2), pre=("b", 1)),
        Version((1, 2), pre=("b", 2)),
        Version((1, 2), pre=("rc", 0)),
        Version((1, 2, 0)),
        Version((1, 2, 1)),
        Version((1, 2, 3, 0)),
        Version((1, 2, 3, 1)),
        Version(2),
        Version((2, 1)),
        Version(epoch=0, release=1),
        Version(epoch=0, release=(1, 1)),
        Version(epoch=0, release=(1, 2)),
        Version(epoch=0, release=(1, 2), post=1),
        Version(epoch=1, release=1),
        Version(epoch=2, release=1),
    ]
    for before, after in zip(versions, versions[1:]):
        assert before < after

    sorted_versions = sorted(versions)
    assert sorted_versions == versions

    reverse_versions = sorted(versions, reverse=True)
    for before, after in zip(reverse_versions, reverse_versions[1:]):
        assert before > after


@pytest.mark.parametrize(
    ["initial", "args", "expected"],
    [
        [Version(0), ["major"], Version(1)],
        [Version(0), ["minor"], Version((0, 1))],
        [Version(0), ["micro"], Version((0, 0, 1))],
        [Version((0, 1)), ["release"], Version((0, 2))],
        [Version((0, 1, 2, 3)), ["release"], Version((0, 1, 2, 4))],
        [Version((1, 2, 3)), ["minor"], Version((1, 3))],
        [Version((1, 2, 3)), ["micro"], Version((1, 2, 4))],
        [Version((1, 2, 3)), ["micro", -1], Version((1, 2, 2))],
        [Version((1, 2, 3)), ["micro", 2], Version((1, 2, 5))],
        [Version((1, 2, 3)), ["major", 2], Version(3)],
        [Version((1, 2, 3)), ["pre"], Version((1, 2, 3), pre=("a", 1))],
        [Version((1, 2, 3)), ["dev"], Version((1, 2, 3), dev=1)],
        [Version((1, 2, 3)), ["post"], Version((1, 2, 3), post=1)],
        [Version((1, 2, 3), ("b", 4)), ["pre"], Version((1, 2, 3), ("b", 5))],
        [Version((1, 2, 3), ("b", 4), 5), ["post"], Version((1, 2, 3), ("b", 4), 6)],
        [Version((1, 2, 3), ("b", 4), 5, 6), ["post"], Version((1, 2, 3), ("b", 4), 6)],
        [Version((1, 2, 3), ("b", 4), 5), ["dev"], Version((1, 2, 3), ("b", 4), 5, 1)],
    ],
)
def test_update(initial: Version, args: Tuple[str, int], expected: Version) -> None:
    assert initial.update(*args) == expected


@pytest.mark.parametrize(
    ["initial", "args", "expected"],
    [
        [Version(0), ["major"], Version(1)],
        [Version(0), [0], Version(1)],
        [Version(0), ["minor"], Version((0, 1))],
        [Version(0), [1], Version((0, 1))],
        [Version(0), ["micro"], Version((0, 0, 1))],
        [Version(0), [2], Version((0, 0, 1))],
        [Version((0, 1, 2)), [-1], Version((0, 1, 3))],
        [Version((0, 1, 2, 3)), [-1], Version((0, 1, 2, 4))],
        [Version((0, 1, 2, 3, 4)), [3, 11], Version((0, 1, 2, 14))],
        [Version((0, 1, 2, 3, 4)), [1], Version((0, 2))],
    ],
)
def test_update_release(initial: Version, args: Tuple[int, int], expected: Version) -> None:
    assert initial.update_release(*args) == expected


@pytest.mark.parametrize(
    ["initial", "keep", "expected"],
    [
        [Version((0, 0, 0, 1)), 0, Version((0, 0, 0, 1))],
        [Version((0, 0, 0, 0)), 0, Version((0))],
        [Version((0, 0, 0, 0)), 2, Version((0, 0))],
        [Version((1, 0, 0, 0)), 2, Version((1, 0))],
    ],
)
def test_strip_release(initial: Version, keep: int, expected: Version) -> None:
    assert initial.strip_release(keep) == expected


@pytest.mark.parametrize(
    ["initial", "keep", "expected"],
    [
        [Version((0, 0, 0, 1)), 1, Version((0))],
        [Version((0, 0, 0, 0)), 2, Version((0, 0))],
        [Version((1, 0, 0, 0)), 2, Version((1, 0))],
        [Version((1, 0, 1)), 2, Version((1, 0))],
    ],
)
def test_truncate_release(initial: Version, keep: int, expected: Version) -> None:
    assert initial.truncate_release(keep) == expected


def test_final() -> None:
    assert Version(1).is_final()
    assert Version((1, 2, 3)).is_final()
    assert Version(epoch=2, release=0).is_final()
    assert not Version(1, ("rc", 11)).is_final()
    assert not Version(1, post=0).is_final()
    assert not Version(1, dev=0).is_final()
    assert not Version(1, local=0).is_final()


@pytest.mark.parametrize(
    ["left", "right", "part"],
    [
        [Version(0), Version(1), "major"],
        [Version(epoch=1, release=0), Version(1), "epoch"],
        [Version((0, 1)), Version(0), "minor"],
        [Version((0, 1, 2)), Version(0), "minor"],
        [Version((0, 1, 2)), Version((0, 1)), "micro"],
        [Version((0, 1, 2)), Version((0, 1, 2)), None],
        [Version((0, 1, 2, 4)), Version((0, 1, 2)), "release"],
        [Version(0, ("a", 0)), Version(0), "pre"],
        [Version(0, ("a", 0)), Version(0, ("a", 1)), "pre"],
        [Version(0, ("a", 0)), Version(0, ("b", 0)), "pre"],
        [Version(0, ("a", 0)), Version(0, ("rc", 0)), "pre"],
        [Version(0, ("b", 0)), Version(0, ("rc", 0)), "pre"],
        [Version(0, ("a", 0), 1), Version(0, ("a", 0)), "post"],
        [Version(0, ("a", 0), 1, 1), Version(0, ("a", 0)), "post"],
        [Version(0, ("a", 0), 0, 0), Version(0, ("a", 0), 0), "dev"],
    ],
)
def test_different_at(left: Version, right: Version, part: VersionPart) -> None:
    if part is not None and not isinstance(part, VersionPart):
        part = VersionPart(part)
    assert left.different_at(right) == part
