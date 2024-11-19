from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# from typing import Annotated
# from typer import Option


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_attribute_docstrings=True,
    )

    def __rich_repr__(self):  # type: ignore
        for field in self.model_fields:
            yield field, getattr(self, field, None), None


#   @classmethod
#   def model_typer_options( cls ) -> dict[str, Option]:
#       return { field: Annotated[ field.type, Option(
#       )] for field in cls.__fields__.keys() }
