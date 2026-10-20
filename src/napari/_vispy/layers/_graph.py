from __future__ import annotations
from typing import TYPE_CHECKING

from napari._vispy.layers.base import VispyBaseLayer
from napari._vispy.utils.qt_font import FontInfo
import numpy as np
from napari._vispy.visuals._graph import _GraphVisual

if TYPE_CHECKING:
    from napari.layers._graph._graph import _Graph


class _VispyGraphLayer(VispyBaseLayer):
    def __init__(self, layer: _Graph, font_info: FontInfo) -> None:
        node: _GraphVisual
        layer: _Graph

        super().__init__(
            layer,
            _GraphVisual(
                font_info
            ),  # pyrefly: ignore [bad-argument-type] # type: ignore[reportArgumentType]
            font_info=font_info,
        )

        self._on_data_change()

    def _on_data_change(self) -> None:
        graph_slice = self.layer._slicing_state.view

        # Nodes are [Node, Coordinates] we need to reverse coordinates from napari zyx to
        # vispy xyz
        nodes = graph_slice.node_coordinates[:, ::-1]
        # Same principle here for reversal
        # Edges are [Edges, Endpoints, Coordinates]
        edges = graph_slice.edge_coordinates[:, :, ::-1]
        edges = edges.reshape(-1, edges.shape[-1])

        # 2D positions need to be 3D for vispy if we don't want to do
        # some buffer resets later
        if nodes.shape[1] == 2:
            nodes = np.pad(nodes, ((0, 0), (0, 1)))
        if edges.shape[1] == 2:
            edges = np.pad(edges, ((0, 0), (0, 1)))

        if len(nodes) == 0:
            nodes = np.zeros((1, nodes.shape[1]))
            size = 0
        else:
            size = 10

        self.node.node_markers.set_data(
            pos=nodes,
            size=size,
            symbol='o',
            edge_color='black',
            face_color='white',
        )

        self.node.edge_markers.visible = len(edges) > 0
        if len(edges) > 0:
            self.node.edge_markers.set_data(
                pos=edges,
                color='white',
                width=1,
            )
