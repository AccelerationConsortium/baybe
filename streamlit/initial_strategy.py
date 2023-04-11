# TODO: Currently, the subclass detection mechanisms (registering via __init_subclass__
#   or using subclasses_recursive) do not work because the base classes and subclasses
#   lie in different files and their code is not necessarily executed. Hence the
#   explicit import that triggers code execution as a temporary workaround.
# flake8: noqa
# pylint: disable=unused-import
"""
This script allows comparing initial selection strategies on different data sets.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydantic
import streamlit as st

from baybe.parameters import NumericDiscrete
from baybe.searchspace import SearchSpace
from baybe.strategies.clustering import KMeansClusteringRecommender
from baybe.strategies.recommender import NonPredictiveRecommender
from baybe.strategies.sampling import FPSRecommender, RandomRecommender
from baybe.utils import isabstract, subclasses_recursive
from sklearn.datasets import make_blobs


def uniform_distribution(n_points: int) -> np.ndarray:
    """Uniformly distributed point generation."""
    return np.random.rand(n_points, 2)


def gaussian_mixture_model(
    n_points: int,
    n_mixtures: int = 3,
    mixture_std: float = 1.0,
) -> np.ndarray:
    """Point generation via Gaussian mixture model."""
    points, *_ = make_blobs(
        n_samples=n_points,
        centers=n_mixtures,
        cluster_std=mixture_std,
    )
    return points


def plot_point_selection(points, selection, title):
    """Visualizes a point selection and the corresponding selection order."""
    fig = go.Figure(data=go.Scatter(x=points[:, 0], y=points[:, 1], mode="markers"))
    for step, _ in enumerate(selection):
        fig.add_annotation(
            x=points[selection[step], 0],
            y=points[selection[step], 1],
            text=str(step),
            arrowcolor="#8b0000",
        )
    fig.update_layout(
        title={
            "text": title,
            "y": 0.85,
        },
        template="seaborn",
    )
    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )
    return fig


# collect all available data distributions
data_distributions = {
    "Uniform": uniform_distribution,
    "Gaussian Mixture Model": gaussian_mixture_model,
}

# collect all available strategies
selection_strategies = {
    cls.type: cls
    for cls in subclasses_recursive(NonPredictiveRecommender)
    if not isabstract(cls)
}


def main():
    """Creates the streamlit dashboard."""

    # fix issue with streamlit and pydantic
    # https://github.com/streamlit/streamlit/issues/3218
    pydantic.class_validators._FUNCS.clear()  # pylint: disable=protected-access

    # show docstring in dashboard
    st.info(__doc__)

    # simulation parameters
    random_seed = int(st.sidebar.number_input("Random seed", value=42))
    strategy_name = st.sidebar.selectbox("Strategy", list(selection_strategies.keys()))
    n_points = st.sidebar.slider("Number of points to be generated", 10, 100, value=50)
    n_selected = st.sidebar.slider(
        "Number of points to be selected",
        1,
        n_points,
        value=int(np.ceil(n_points / 10)),
    )
    distribution = st.sidebar.selectbox(
        "Data distribution", list(data_distributions.keys())
    )

    # set the distribution options
    if distribution == "Gaussian Mixture Model":
        distribution_params = {
            "n_mixtures": st.sidebar.number_input("Number of mixtures", 1, value=2),
            "mixture_std": st.sidebar.slider("Mixture size", 0.0, 1.0, value=1.0),
        }
    else:
        distribution_params = {}

    # fix the random seed
    np.random.seed(random_seed)

    # create the points
    points = pd.DataFrame(
        data_distributions[distribution](n_points, **distribution_params)
    )

    # create the corresponding search space
    # TODO[11815]: We need an easy way to create search spaces from DataFrames
    searchspace = SearchSpace.create(
        parameters=[NumericDiscrete(name="bla", values=[1, 2, 3])],
        empty_encoding=True,
    )
    searchspace.discrete.comp_rep = points
    searchspace.discrete.exp_rep = points
    searchspace.discrete.metadata = pd.DataFrame(
        {"dont_recommend": False, "was_recommended": False, "was_measured": False},
        index=points.index,
    )

    # create the strategy and generate the recommendations
    # TODO: The acquisition function should become optional for model-free methods
    strategy = selection_strategies[strategy_name]()
    selection = strategy.recommend(searchspace=searchspace, batch_quantity=n_selected)

    # show the result
    fig = plot_point_selection(points.values, selection.index.values, strategy_name)
    st.plotly_chart(fig)


if __name__ == "__main__":
    main()
