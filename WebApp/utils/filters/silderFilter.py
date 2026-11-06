from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QStyle, QStyleOptionSlider


class SliderFilter(QObject):
  """Event filter that blocks groove-clicking while allowing dragging."""

  def eventFilter(self, obj, event):
    if event.type() == QEvent.MouseButtonPress:
      opt = QStyleOptionSlider()
      obj.initStyleOption(opt)

      # Get the handle bounding rectangle
      handle_rect = obj.style().subControlRect(
          QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, obj
      )

      # If the click is NOT on the handle, block it
      if not handle_rect.contains(event.pos()):
        return True  # 'True' consumes the event, stopping it from jumping

    return super().eventFilter(obj, event)