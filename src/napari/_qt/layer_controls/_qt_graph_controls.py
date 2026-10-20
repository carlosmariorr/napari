from __future__ import annotations

from typing import TYPE_CHECKING
from napari._qt.layer_controls.qt_layer_controls_base import QtLayerControls
from napari._qt.widgets.qt_mode_buttons import QtModeRadioButton

if TYPE_CHECKING:
    from napari.layers._graph._graph import _Graph


class _QtGraphControls(QtLayerControls):
    def __init__(self, layer: _Graph) -> None:
        super().__init__(layer)
        self.transform_button.hide()

    def _radio_button(
        self,
        layer,
        btn_name,
        mode,
        edit_button,
        action_name,
        extra_tooltip_text='',
        **kwargs,
    ):
        button = QtModeRadioButton(layer, btn_name, mode, **kwargs)
        self._MODE_BUTTONS[mode] = button
        self.button_group.addButton(button)
        if edit_button:
            self._EDIT_BUTTONS += (button,)
        return button
