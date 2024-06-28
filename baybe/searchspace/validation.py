"""Validation functionality for search spaces."""

from collections.abc import Collection, Sequence

import pandas as pd

from baybe.exceptions import EmptySearchSpaceError
from baybe.parameters import TaskParameter
from baybe.parameters.base import Parameter


def validate_parameter_names(  # noqa: DOC101, DOC103
    parameters: Collection[Parameter],
) -> None:
    """Validate the parameter names.

    Raises:
        ValueError: If the given list contains parameters with the same name.
    """
    param_names = [p.name for p in parameters]
    if len(set(param_names)) != len(param_names):
        raise ValueError("All parameters must have unique names.")


def validate_parameters(parameters: Collection[Parameter]) -> None:  # noqa: DOC101, DOC103
    """Validate the parameters.

    Raises:
        EmptySearchSpaceError: If the parameter list is empty.
        NotImplementedError: If more than one
            :class:`baybe.parameters.categorical.TaskParameter` is requested.
    """
    if not parameters:
        raise EmptySearchSpaceError("At least one parameter must be provided.")

    # TODO [16932]: Remove once more task parameters are supported
    if len([p for p in parameters if isinstance(p, TaskParameter)]) > 1:
        raise NotImplementedError(
            "Currently, at most one task parameter can be considered."
        )

    # Assert: unique names
    validate_parameter_names(parameters)


def get_transform_parameters(
    parameters: Sequence[Parameter],
    df: pd.DataFrame,
    allow_missing: bool,
    allow_extra: bool,
):
    """Extract the parameters relevant for transforming a given dataframe."""
    parameter_names = [p.name for p in parameters]

    if (not allow_missing) and (missing := set(parameter_names) - set(df)):
        raise ValueError(
            f"The search space parameter(s) {missing} cannot be matched against "
            f"the provided dataframe. If you want to transform a subset of "
            f"parameter columns, explicitly set `allow_missing=True`."
        )

    if (not allow_extra) and (extra := set(df) - set(parameter_names)):
        raise ValueError(
            f"The provided dataframe column(s) {extra} cannot be matched against"
            f"the search space parameters. If you want to transform a dataframe "
            f"with additional columns, explicitly set `allow_extra=True'."
        )

    return [p for p in parameters if p.name in df] if allow_missing else parameters
