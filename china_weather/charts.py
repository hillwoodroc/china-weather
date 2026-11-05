"""Small native GTK trend plot; exact values are also shown in accessible rows."""
from .i18n import translate as _
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class TrendChart(Gtk.DrawingArea):
    def __init__(self, rows, field, unit):
        super().__init__(content_height=210, hexpand=True)
        self.rows, self.field, self.unit = rows, field, unit
        self.set_draw_func(self.draw)
        self.set_tooltip_text(_('时间从左到右排列；具体数值见下方列表。断点表示缺测。'))

    def draw(self, area, cr, width, height):
        values = [row.get(self.field) for row in self.rows]
        valid = [value for value in values if value is not None]
        if not valid:
            return
        low, high = min(valid), max(valid)
        if self.field in ('rain', 'wind', 'humidity'):
            low = 0
        if self.field == 'humidity':
            high = 100
        span = max(high - low, 1)
        left, top, plot_width, plot_height = 65, 20, max(width - 85, 1), height - 62
        color = self.get_style_context().get_color()
        cr.select_font_face('Sans')
        cr.set_font_size(11)
        for step in range(5):
            y = top + plot_height * step / 4
            cr.set_source_rgba(color.red, color.green, color.blue, .15)
            cr.move_to(left, y)
            cr.line_to(left + plot_width, y)
            cr.stroke()
            cr.set_source_rgba(color.red, color.green, color.blue, .8)
            cr.move_to(2, y + 4)
            cr.show_text(f'{low + span * (1 - step / 4):.1f}')
        cr.set_line_width(2)
        cr.set_source_rgb(.21, .52, .89)
        connected = False
        for index, value in enumerate(values):
            x = left + index * plot_width / max(len(values) - 1, 1)
            if value is None:
                cr.stroke()
                connected = False
                continue
            y = top + (1 - (value - low) / span) * plot_height
            if connected:
                cr.line_to(x, y)
            else:
                cr.move_to(x, y)
            connected = True
        cr.stroke()
        for index, value in enumerate(values):
            if value is not None:
                x = left + index * plot_width / max(len(values) - 1, 1)
                y = top + (1 - (value - low) / span) * plot_height
                cr.arc(x, y, 2.5, 0, 6.2832)
                cr.fill()
        cr.set_source_rgba(color.red, color.green, color.blue, .8)
        cr.move_to(left, height - 12)
        cr.show_text(self.rows[0]['time'])
        if len(self.rows) > 1:
            text = self.rows[-1]['time']
            cr.move_to(max(left, width - 105), height - 12)
            cr.show_text(text)
