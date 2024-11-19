import pytest
from tag_sensor.family import (
    Family,
    get_family,
    get_family_size,
    FamilyNotFoundError,
    TagIdTooLargeError,
)


def test_family_4():
    family = Family("4X4")
    assert isinstance(family, Family)
    assert family.grid_size == 4
    assert str(family) == "4X4"

    assert get_family("4X4") == family


def test_family_5():
    family = Family("5X5")
    assert isinstance(family, Family)
    assert family.grid_size == 5
    assert str(family) == "5X5"


def test_bad_family_group():
    with pytest.raises(FamilyNotFoundError):
        Family("bad_family")  # type: ignore


def test_get_family_size():
    assert get_family_size(0) == 50
    assert get_family_size(1) == 50
    assert get_family_size(49) == 50
    assert get_family_size(50) == 100
    assert get_family_size(75) == 100
    assert get_family_size(99) == 100
    assert get_family_size(100) == 250
    assert get_family_size(250) == 1000
    assert get_family_size(999) == 1000

    with pytest.raises(TagIdTooLargeError):
        get_family_size(1000)
