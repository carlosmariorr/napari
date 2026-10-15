from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from vispy import gloo

from napari._vispy.layers.base import VispyBaseLayer
from napari._vispy.visuals._graph import _GraphVisual

if TYPE_CHECKING:
    from napari._vispy.utils.qt_font import FontInfo
    from napari.layers._graph._graph import _Graph


class _VispyGraphLayer(VispyBaseLayer):
    node: _GraphVisual
    layer: _Graph

    def __init__(self, layer: _Graph, font_info: FontInfo) -> None:
        super().__init__(layer, _GraphVisual(font_info), font_info=font_info)
        self._on_data_change()

    def _on_data_change(self) -> None:
        graph_slice = self.layer._slicing_state._view

        nodes = graph_slice.node_coordinates[:, ::-1]
        edges = graph_slice.edge_coordinates[:, :, ::-1]
        edges = edges.reshape(-1, edges.shape[-1])

        # The 2D layer needs a zero z coordinate in a 3D view.
        if self.layer._slice_input.ndisplay == 3 and self.layer.ndim == 2:
            nodes = np.pad(nodes, ((0, 0), (0, 1)))
            edges = np.pad(edges, ((0, 0), (0, 1)))

        # Vispy markers need one invisible point when the slice is empty.
        if len(nodes) == 0:
            nodes = np.zeros((1, nodes.shape[1]))
            size = 0
        else:
            size = 8

        self.node.node_markers.set_data(
            pos=nodes,
            size=size,
            symbol='o',
            edge_color='black',
            face_color='white',
        )

        self.node.edge_markers.visible = len(edges) > 0
        if len(edges) > 0:
            # Vispy's line position buffer keeps its original coordinate
            # dimension. Replace it when switching between 2D and 3D data.
            self.node.edge_markers._line_visual._pos_vbo = gloo.VertexBuffer()
            self.node.edge_markers.set_data(
                pos=edges,
                color='white',
                width=1,
            )

        self.reset()
