from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Literal, TypeGuard, get_args

from cv2 import aruco
from cv2.aruco import ArucoDetector, DetectorParameters

from .utils import NotFoundError

FamilyGroup = Literal["4X4", "5X5", "6X6", "7X7"]
FamilySize = Literal[50, 100, 250, 1000]


class FamilyNotFoundError(NotFoundError):
    def __init__(self, family: str):
        super().__init__(f'Family "{family}" not found')


class TagIdTooLargeError(ValueError):
    def __init__(self, tag_id: int):
        super().__init__(
            f'Value "{tag_id}" is too large for any ArUco family',
        )


@dataclass
class Family:
    group: FamilyGroup

    def __init__(self, group: FamilyGroup):
        if not is_family_group(group):
            raise FamilyNotFoundError(group)
        self.group = group

    def dictionary(self, max_id: int = 999):
        size = get_family_size(max_id)
        name = f"DICT_{self.group}_{size}"
        dict_id = getattr(aruco, name)
        return aruco.getPredefinedDictionary(dict_id)

    def parameters(self):
        return DetectorParameters()

    def detector(self, max_id: int = 999):
        params = self.parameters()
        return ArucoDetector(self.dictionary(max_id), params)

    @property
    def grid_size(self):
        return int(self.group[0])

    def __hash__(self):
        return hash(self.group)

    def __str__(self):
        return self.group


@cache
def get_family(family: FamilyGroup) -> Family:
    return Family(family)


TAG_FAMILY_XL = 1000
TAG_FAMILY_LG = 250
TAG_FAMILY_MD = 100
TAG_FAMILY_SM = 50


def get_family_size(value: int):
    if value >= TAG_FAMILY_XL:
        raise TagIdTooLargeError(1000)
    if value >= TAG_FAMILY_LG:
        return TAG_FAMILY_XL
    if value >= TAG_FAMILY_MD:
        return TAG_FAMILY_LG
    if value >= TAG_FAMILY_SM:
        return TAG_FAMILY_MD
    if value >= 0:
        return TAG_FAMILY_SM
    raise ValueError  # pragma: no cover


def is_family_group(value: str) -> TypeGuard[FamilyGroup]:
    return value in get_args(FamilyGroup)


ALL_FAMILY_GROUPS = get_args(FamilyGroup)
