from __future__ import annotations

from typing import TYPE_CHECKING

from vispy.visuals import LineVisual

from napari._vispy.visuals.clipping_planes_mixin import ClippingPlanesMixin
from vispy.scene.visuals import Compound, Line

from napari._vispy.visuals.markers import Markers

if TYPE_CHECKING:
    from napari._vispy.utils.qt_font import FontInfo


class _GraphVisual(ClippingPlanesMixin, Compound):
    """
    Compound vispy visual for graph visualization with
    clipping planes functionality

    Components:
        - Markers for nodes (vispy.MarkersVisual)
        - Connected Lines for highlights (vispy.LineVisual)
    """

    def __init__(self, font_info: FontInfo) -> None:
        super().__init__(
            [
                Markers(),
                Line(connect='segments', antialias=True),
            ],
            font_info=font_info,
        )

    @property
    def node_markers(self) -> Markers:
        return self._subvisuals[0]

    @property
    def edge_markers(self) -> LineVisual:
        return self._subvisuals[1]
