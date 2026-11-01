"""Fail closed until a provider feature has an implemented, accepted contract."""
from typing import NoReturn

from fastapi import HTTPException


def feature_unavailable(feature: str) -> NoReturn:
    raise HTTPException(status_code=501, detail={
        "code": "feature_not_available", "feature": feature,
        "message": "This provider feature is not available in the current relay.",
    })
