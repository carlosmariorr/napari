from dataclasses import dataclass
import numpy as np
from networkx import Graph

from napari.layers.base import _LayerSlicingState
from napari.layers.utils._slice_input import _SliceInput, _ThickNDSlice


@dataclass
class _GraphSlice:
    node_coordinates: np.ndarray
    edge_coordinates: np.ndarray


class _GraphSlicingState(_LayerSlicingState):
    def __init__(self, layer, data, cache):
        super().__init__(layer, data, cache)
        self._view = None

    def _set_view_slice(self) -> None:
        self._view = _slice_graph(
            self.layer.data, self._slice_input, self.data_slice
        )


def _slice_graph(
    graph: Graph, slice_input: _SliceInput, data_slice: _ThickNDSlice
) -> _GraphSlice:
    displayed = np.asarray(slice_input.displayed, dtype=int)
    not_displayed = np.asarray(slice_input.not_displayed, dtype=int)
    ndisplay = len(displayed)

    if graph.number_of_nodes() == 0:
        return _GraphSlice(
            node_coordinates=np.empty((0, ndisplay)),
            edge_coordinates=np.empty((0, 2, ndisplay)),
        )

    node_ids = list(graph.nodes)
    coordinates = np.asarray(
        [graph.nodes[node_id]['coordinates'] for node_id in node_ids],
        dtype=float,
    )

    point, margin_left, margin_right = data_slice.as_array()
    low = point - margin_left
    high = point + margin_right

    # I decided to do the zero width just like points do,
    # and render -0.5 and 0.5 down and up respectively
    zero_width = np.isclose(low, high)
    low[zero_width] -= 0.5
    high[zero_width] += 0.5

    if not_displayed.size:
        coords_to_check = coordinates[:, not_displayed]
        nodes_in_slice = np.all(
            (coords_to_check >= low[not_displayed])
            & (coords_to_check <= high[not_displayed]),
            axis=1,
        )
    else:
        nodes_in_slice = np.ones(len(node_ids), dtype=bool)

    visible_nodes = coordinates[nodes_in_slice][:, displayed]

    node_index = {node_id: idx for idx, node_id in enumerate(node_ids)}
    edge_segments = []

    for source, target in graph.edges:
        start = coordinates[node_index[source]]
        end = coordinates[node_index[target]]
        direction = end - start

        edge_fraction_enter = 0.0
        edge_fraction_exit = 1.0
        intersects = True

        for axis in not_displayed:
            axis = int(axis)
            if np.isclose(direction[axis], 0):
                # The edge is parallel to this slice dimension.
                if not low[axis] <= start[axis] <= high[axis]:
                    intersects = False
                    break
                continue

            # This calculates the intersection to both lower and higher limits
            # of the not displayed axis. If the intersection is less than 0
            # or more than 1, then it'll just use the minimum or maximum (0 or 1).
            # If its inside, it'll calculate the enter and end fractions and flag it
            # as an intersecting edge
            intersect_low = (low[axis] - start[axis]) / direction[axis]
            intersect_high = (high[axis] - start[axis]) / direction[axis]

            edge_fraction_enter = max(
                edge_fraction_enter, min(intersect_low, intersect_high)
            )
            edge_fraction_exit = min(
                edge_fraction_exit, max(intersect_low, intersect_high)
            )

            if edge_fraction_enter > edge_fraction_exit:
                intersects = False
                break

        # If the edge intersects the rendered volume in the non visible axis,
        # it calculates the length of the edge based on the enter and exit fractions
        if intersects:
            clipped_start = start + edge_fraction_enter * direction
            clipped_end = start + edge_fraction_exit * direction

            edge_segments.append(
                np.stack((clipped_start[displayed], clipped_end[displayed]))
            )

    edge_coordinates = np.asarray(edge_segments, dtype=float).reshape(
        -1, 2, ndisplay
    )
    return _GraphSlice(
        node_coordinates=visible_nodes, edge_coordinates=edge_coordinates
    )
