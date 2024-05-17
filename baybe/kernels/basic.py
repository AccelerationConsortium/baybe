"""Collection of basic kernels."""

from typing import Optional

from attrs import define, field
from attrs.converters import optional as optional_c
from attrs.validators import gt, in_, instance_of
from attrs.validators import optional as optional_v

from baybe.kernels.base import Kernel
from baybe.priors.base import Prior
from baybe.utils.conversion import fraction_to_float
from baybe.utils.validation import finite_float


@define(frozen=True)
class CosineKernel(Kernel):
    """A cosine kernel."""

    period_length_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel periodic length."""

    period_length_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel periodic length."""

    def to_gpytorch(self, *args, **kwargs):  # noqa: D102
        # See base class.
        import torch

        from baybe.utils.torch import DTypeFloatTorch

        gpytorch_kernel = super().to_gpytorch(*args, **kwargs)
        if (initial_value := self.period_length_initial_value) is not None:
            gpytorch_kernel.period_length = torch.tensor(
                initial_value, dtype=DTypeFloatTorch
            )
        return gpytorch_kernel


@define(frozen=True)
class LinearKernel(Kernel):
    """A linear kernel."""

    variance_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the variance parameter."""

    variance_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the variance parameter."""

    def to_gpytorch(self, *args, **kwargs):  # noqa: D102
        # See base class.
        import torch

        from baybe.utils.torch import DTypeFloatTorch

        gpytorch_kernel = super().to_gpytorch(*args, **kwargs)
        if (initial_value := self.variance_initial_value) is not None:
            gpytorch_kernel.variance = torch.tensor(
                initial_value, dtype=DTypeFloatTorch
            )
        return gpytorch_kernel


@define(frozen=True)
class MaternKernel(Kernel):
    """A Matern kernel using a smoothness parameter."""

    nu: float = field(
        converter=fraction_to_float, validator=in_([0.5, 1.5, 2.5]), default=2.5
    )
    """A smoothness parameter.

    Only takes the values 0.5, 1.5 or 2.5. Larger values yield smoother interpolations.
    """

    lengthscale_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel lengthscale."""

    lengthscale_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel lengthscale."""


@define(frozen=True)
class PeriodicKernel(Kernel):
    """A periodic kernel."""

    lengthscale_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel lengthscale."""

    lengthscale_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel lengthscale."""

    period_length_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel periodic length."""

    period_length_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel periodic length."""

    def to_gpytorch(self, *args, **kwargs):  # noqa: D102
        # See base class.
        import torch

        from baybe.utils.torch import DTypeFloatTorch

        gpytorch_kernel = super().to_gpytorch(*args, **kwargs)
        # lengthscale is handled by the base class

        if (initial_value := self.period_length_initial_value) is not None:
            gpytorch_kernel.period_length = torch.tensor(
                initial_value, dtype=DTypeFloatTorch
            )
        return gpytorch_kernel


@define(frozen=True)
class PiecewisePolynomialKernel(Kernel):
    """A piecewise polynomial kernel."""

    q: float = field(converter=int, validator=in_([0, 1, 2, 3]), default=2)
    """A smoothness parameter."""

    lengthscale_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel lengthscale."""

    lengthscale_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel lengthscale."""


@define(frozen=True)
class PolynomialKernel(Kernel):
    """A polynomial kernel."""

    power: int = field(converter=int)
    """The power of the polynomial term."""

    offset_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel offset."""

    offset_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel offset."""

    def to_gpytorch(self, *args, **kwargs):  # noqa: D102
        # See base class.
        import torch

        from baybe.utils.torch import DTypeFloatTorch

        gpytorch_kernel = super().to_gpytorch(*args, **kwargs)

        if (initial_value := self.offset_initial_value) is not None:
            gpytorch_kernel.offset = torch.tensor(initial_value, dtype=DTypeFloatTorch)
        return gpytorch_kernel


@define(frozen=True)
class RBFKernel(Kernel):
    """A radial basis function (RBF) kernel."""

    lengthscale_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel lengthscale."""

    lengthscale_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel lengthscale."""


@define(frozen=True)
class RFFKernel(Kernel):
    """A random Fourier features (RFF) kernel."""

    num_samples: int = field(converter=int, validator=gt(0))
    """The number of frequencies to draw."""

    lengthscale_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel lengthscale."""

    lengthscale_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel lengthscale."""


@define(frozen=True)
class RQKernel(Kernel):
    """A rational quadratic (RQ) kernel."""

    lengthscale_prior: Optional[Prior] = field(
        default=None, validator=optional_v(instance_of(Prior))
    )
    """An optional prior on the kernel lengthscale."""

    lengthscale_initial_value: Optional[float] = field(
        default=None, converter=optional_c(float), validator=optional_v(finite_float)
    )
    """An optional initial value for the kernel lengthscale."""
