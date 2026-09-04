from __future__ import annotations

import numpy as np
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QWidget

from napari._app_model import get_app_model
from napari._qt.layer_controls.dynamic.widgets.qt_widget_controls_base import (
    QtWidgetControlsBase,
    QtWrappedLabel,
)
from napari._qt.utils import qt_signals_blocked
from napari._qt.widgets.qt_mode_buttons import QtModePushButton
from napari.utils.misc import human_readable_size

from napari.layers import Image, Labels


def _format_level_label(
    index: int,
    shape: tuple,
    nbytes: int,
) -> str:
    """Build a human-readable label for one multiscale level.

    Parameters
    ----------
    index : int
        Zero-based level index.
    shape : tuple of int
        Full shape of the array at this level.
    nbytes : int
        Size of the array in bytes.

    Returns
    -------
    str
        e.g. ``"0: 256 x 256 x 128 (8.4 MB)"``
    """
    shape_str = ' \u00d7 '.join(str(s) for s in shape)
    size_str = human_readable_size(nbytes)
    return f'{index}: {shape_str} ({size_str})'


class QtMultiscaleLevelControl(QtWidgetControlsBase):
    """Widget to manually select which multiscale level to render.

    Shows a combobox with "Auto" plus one entry per resolution level.
    Only visible when the layer is multiscale.

    Parameters
    ----------
    parent : QWidget
        Parent widget.
    layer : list[napari.layers.Layer]
        A list of napari layers.

    Attributes
    ----------
    level_combobox : QComboBox
        Combobox listing "Auto" and each resolution level.
    level_label : QtWrappedLabel
        Label for the resolution combobox.
    """

    _layers: list[Image | Labels]

    def __init__(
        self, layers: list[Image | Labels], parent: QWidget | None = None
    ) -> None:
        super().__init__(layers, parent)  # type: ignore

        self.resolution_row = QWidget()
        resolution_layout = QHBoxLayout(self.resolution_row)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(2)

        self.level_extraction_button = QtModePushButton(
            layer=layers[0],
            button_name='histogram',
            tooltip='Extract selected data level to new layer',
            slot=self._on_extract_data_level_button_pressed,
        )
        self.level_combobox = QComboBox(parent)

        resolution_layout.addWidget(self.level_combobox)
        resolution_layout.addWidget(self.level_extraction_button)

        self.level_label = QtWrappedLabel('resolution:')

        # Only set up and show widgets if layer is multiscale
        if all(
            layer.multiscale
            and np.array_equal(
                layer.level_shapes, self._layers[0].level_shapes
            )
            for layer in self._layers
        ):
            self._update_level_labels()
            self.level_combobox.currentIndexChanged.connect(
                self._on_combobox_changed
            )
            for layer in self._layers:
                layer.events.locked_data_level.connect(
                    self._on_locked_data_level_change
                )
                layer.events.data.connect(
                    self._update_level_labels
                )  # TODO: should this connection also happen when data is not multiscale
                layer.events.set_data.connect(self._update_auto_label)
            self.level_extraction_button.show()
            self.level_combobox.show()
            self.level_label.show()
        else:
            self.level_extraction_button.hide()
            self.level_combobox.hide()
            self.level_label.hide()

    def _update_level_labels(self) -> None:
        """Populate the combobox with resolution level labels."""
        with qt_signals_blocked(self.level_combobox):
            self.level_combobox.clear()
            self.level_combobox.addItem('Auto', None)

            if all(layer.multiscale for layer in self._layers):
                shapes = self._layers[0].level_shapes
                itemsize = self._layers[0].dtype.itemsize
                for i, shape in enumerate(shapes):
                    # Calculate size using full shape
                    nbytes = int(np.prod(shape) * itemsize)

                    label = _format_level_label(i, tuple(shape), nbytes)
                    self.level_combobox.addItem(label, i)

            # Reflect current locked state
            locked = getattr(self._layers[0], '_locked_data_level', None)
            if locked is not None:
                # +1 because index 0 is "Auto"
                self.level_combobox.setCurrentIndex(locked + 1)
            else:
                self.level_combobox.setCurrentIndex(0)

            self._update_auto_label()

    def _update_auto_label(self) -> None:
        """Update the 'Auto' entry to show the currently rendered level."""
        label = f'Auto ({self._layers[0].data_level})'
        if self.level_combobox.itemText(0) != label:
            self.level_combobox.setItemText(0, label)

    def _on_combobox_changed(self, index: int) -> None:
        """Update the layer's locked data level from the combobox selection.

        Parameters
        ----------
        index : int
            Index of the selected combobox item. ``0`` corresponds to
            "Auto" (``None``); higher indices map to resolution levels.
        """
        level = self.level_combobox.itemData(index)
        for layer in self._layers:
            layer.locked_data_level = level

    def _on_locked_data_level_change(self) -> None:
        """Sync the combobox when locked_data_level is set programmatically."""
        locked = self._layers[0].locked_data_level
        with qt_signals_blocked(self.level_combobox):
            if locked is not None:
                self.level_combobox.setCurrentIndex(locked + 1)
            else:
                self.level_combobox.setCurrentIndex(0)

    def _on_extract_data_level_button_pressed(self) -> None:
        """Extract the data levels of the layers to new layers using the _layer_actions methods"""
        get_app_model().commands.execute_command(
            'napari.layer.extract_multiscale_level',
            level=self.level_combobox.currentData(),
        )

    def get_widget_controls(
        self,
    ) -> list[tuple[QtWrappedLabel, QWidget] | tuple[QWidget]]:
        """Return the label/widget pairs for this control.

        Returns
        -------
        list[tuple[QtWrappedLabel, QWidget] | tuple[QWidget]]
            Single-element list containing the resolution label and combobox.
        """
        return [(self.level_label, self.resolution_row)]
