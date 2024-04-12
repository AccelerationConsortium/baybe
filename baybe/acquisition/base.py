"""Base classes for all acquisition functions."""

from __future__ import annotations

import warnings
from abc import ABC
from inspect import signature
from typing import ClassVar, Union

import pandas as pd
from attrs import define

from baybe.acquisition.adapter import AdapterModel
from baybe.serialization.core import (
    converter,
    get_base_structure_hook,
    unstructure_base,
)
from baybe.serialization.mixin import SerialMixin
from baybe.surrogates.base import Surrogate
from baybe.utils.basic import filter_attributes
from baybe.utils.dataframe import to_tensor


@define(frozen=True)
class AcquisitionFunction(ABC, SerialMixin):
    """Abstract base class for all acquisition functions."""

    _abbreviation: ClassVar[str]
    """An alternative name for type resolution."""

    @classmethod
    @property
    def is_mc(cls) -> bool:
        """Flag indicating whether this is a Monte-Carlo acquisition function."""
        return cls._abbreviation.startswith("q")

    def to_botorch(
        self,
        surrogate: Surrogate,
        train_x: pd.DataFrame,
        train_y: pd.DataFrame,
    ):
        """Create the botorch-ready representation of the function."""
        import botorch.acquisition as botorch_analytical_acqf

        acqf_cls = getattr(botorch_analytical_acqf, self.__class__.__name__)
        fields_dict = filter_attributes(object=self, callable_=acqf_cls.__init__)

        if not self.is_mc:
            best_f = train_y.max().item()

            if "best_f" in signature(acqf_cls).parameters:
                fields_dict.update({"best_f": best_f})

            botorch_acqf = acqf_cls(AdapterModel(surrogate), **fields_dict)
        else:
            from botorch.acquisition.factory import get_acquisition_function
            from botorch.acquisition.objective import IdentityMCObjective

            botorch_acqf = get_acquisition_function(
                acquisition_function_name=self._abbreviation,
                model=AdapterModel(surrogate),
                X_observed=to_tensor(train_x),
                objective=IdentityMCObjective(),
                **fields_dict,  # optional parameters like beta
            )

        return botorch_acqf


# Register de-/serialization hooks
def _add_deprecation_hook(hook):
    """Add deprecation warnings to the default hook.

    Used for backward compatibility only and will be removed in future versions.
    """

    def added_deprecation_hook(val: Union[dict, str], cls: type):
        UCB_DEPRECATIONS = {
            "VarUCB": "UpperConfidenceBound",
            "qVarUCB": "qUpperConfidenceBound",
        }
        if (entry := val if isinstance(val, str) else val["type"]) in UCB_DEPRECATIONS:
            warnings.warn(
                f"The use of `{entry}` is deprecated and will be disabled in a "
                f"future version. The get the same outcome, use the new "
                f"`{UCB_DEPRECATIONS[entry]}` class instead with a beta of 100.0.",
                DeprecationWarning,
            )
            val = {"type": UCB_DEPRECATIONS[entry], "beta": 100.0}

        return hook(val, cls)

    return added_deprecation_hook


converter.register_structure_hook(
    AcquisitionFunction,
    _add_deprecation_hook(get_base_structure_hook(AcquisitionFunction)),
)
converter.register_unstructure_hook(AcquisitionFunction, unstructure_base)
