"""
Test for continuous parameters
"""
import pytest
import torch


@pytest.mark.parametrize(
    "parameter_names",
    [
        ["Conti_finite1"],
        ["Conti_finite2"],
        ["Conti_infinite1"],
        ["Conti_infinite2"],
        ["Conti_infinite3"],
        ["Conti_infinite4"],
        ["Conti_infinite5"],
        ["Conti_finite1", "Conti_finite2", "Conti_infinite5"],
    ],
)
def test_valid_configs(baybe):
    """
    Test whether the given settings work without error
    """

    print(baybe.searchspace.continuous.param_bounds_comp.flatten())

    assert all(
        torch.is_floating_point(itm)
        for itm in baybe.searchspace.continuous.param_bounds_comp.flatten()
    )