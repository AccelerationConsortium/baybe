"""Multi-armed bandit surrogates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from attrs import define, field
from botorch.sampling.base import MCSampler
from botorch.sampling.get_sampler import GetSampler
from torch.distributions import Beta  # TODO: how to import this?!

from baybe.exceptions import IncompatibleSearchSpaceError, ModelNotTrainedError
from baybe.parameters.categorical import CategoricalParameter
from baybe.parameters.enum import CategoricalEncoding
from baybe.priors import BetaPrior
from baybe.searchspace.core import SearchSpace
from baybe.surrogates.base import Surrogate
from baybe.targets.binary import _NEGATIVE_VALUE_COMP, _POSITIVE_VALUE_COMP

if TYPE_CHECKING:
    from botorch.posteriors import TorchPosterior
    from torch import Tensor


@define
class BernoulliMultiArmedBanditSurrogate(Surrogate):
    """A multi-armed bandit model with Bernoulli likelihood and beta prior."""

    joint_posterior: ClassVar[bool] = False
    # See base class.

    supports_transfer_learning: ClassVar[bool] = False
    # See base class.

    prior: BetaPrior = field(factory=lambda: BetaPrior(1, 1))
    """The beta prior for the win rates of the bandit arms. Uniform by default."""

    _win_lose_counts: Tensor | None = field(init=False, default=None, eq=False)
    """Sufficient statistics for the Bernoulli likelihood model."""

    def maximum_a_posteriori_per_arm(self) -> Tensor:
        """Compute the maximum a posteriori win rates for all arms.

        Returns:
            A tensor of length ``N``, where ``N`` is the number of bandit arms.
            Contains ``float('nan')`` for arms with undefined mode.
        """
        from torch.distributions import Beta

        return Beta(*self._posterior_beta_parameters()).mode

    def _posterior_beta_parameters(self) -> Tensor:
        """Compute the posterior parameters of the beta distribution.

        Raises:
            ModelNotTrainedError: If accessed before the model was trained.

        Returns:
            A tensors of shape ``(2, N)`` containing the posterior beta parameters,
            where ``N`` is the number of bandit arms.
        """
        if self._win_lose_counts is None:
            raise ModelNotTrainedError(
                f"'{self.__class__.__name__}' must be trained before posterior "
                f"information can be accessed."
            )
        return self._win_lose_counts + self.prior.to_torch().unsqueeze(-1)

    @staticmethod
    def _make_target_scaler_factory():
        # See base class.
        #
        # We directly use the binary computational representation from the target.
        return None

    def _posterior(self, candidates: Tensor, /) -> TorchPosterior:
        # See base class.

        from botorch.posteriors import TorchPosterior
        from torch.distributions import Beta

        beta_params_for_candidates = self._posterior_beta_parameters().T[
            candidates.argmax(-1)
        ]
        return TorchPosterior(Beta(*beta_params_for_candidates.split(1, -1)))

    def _fit(self, train_x: Tensor, train_y: Tensor, _: Any = None) -> None:
        # See base class.

        # TODO: Fix requirement of OHE encoding. This is likely a long-term goal since
        #   probably requires decoupling parameter from encodings and associating the
        #   latter with the surrogate.
        # TODO: Generalize to arbitrary number of categorical parameters
        match self._searchspace:
            case SearchSpace(
                parameters=[CategoricalParameter(encoding=CategoricalEncoding.OHE)]
            ):
                pass
            case _:
                raise IncompatibleSearchSpaceError(
                    f"'{self.__class__.__name__}' currently only supports search "
                    f"spaces spanned by exactly one categorical parameter using "
                    f"one-hot encoding."
                )

        import torch

        # IMPROVE: The training inputs/targets can actually be represented as
        #   integers/boolean values but the transformation pipeline currently
        #   converts them float. Potentially, this can be improved by making
        #   the type conversion configurable.

        wins = (train_x * (train_y == float(_POSITIVE_VALUE_COMP))).sum(axis=0)
        losses = (train_x * (train_y == float(_NEGATIVE_VALUE_COMP))).sum(axis=0)
        self._win_lose_counts = torch.vstack([wins, losses]).to(torch.int)


class CustomMCSampler(MCSampler):
    """Customer sampler for beta posterior."""

    def forward(self, posterior: TorchPosterior) -> Tensor:
        """Sample the posterior."""
        samples = posterior.rsample(self.sample_shape)
        return samples


@GetSampler.register(Beta)
def get_custom_sampler(_, sample_shape):
    """Get the sampler for the beta posterior."""
    return CustomMCSampler(sample_shape=sample_shape)
