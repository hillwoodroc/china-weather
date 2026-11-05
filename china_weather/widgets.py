"""Scrollable content with adaptive navigation arrows instead of scrollbars."""
from .i18n import translate as _
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk


class ArrowScroller(Gtk.Overlay):
    def __init__(self, child, vertical=False, **kwargs):
        super().__init__(**kwargs)
        self.vertical = vertical
        self.scroll = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER if vertical else Gtk.PolicyType.EXTERNAL,
            vscrollbar_policy=Gtk.PolicyType.EXTERNAL if vertical else Gtk.PolicyType.NEVER,
            hexpand=True, vexpand=vertical)
        self.scroll.set_child(child)
        self.set_child(self.scroll)
        self.adjustment = self.scroll.get_vadjustment() if vertical else self.scroll.get_hadjustment()
        self.back = Gtk.Button(icon_name='go-up-symbolic' if vertical else 'go-previous-symbolic',
                               tooltip_text=_('向上滚动') if vertical else _('向左滚动'))
        self.forward = Gtk.Button(icon_name='go-down-symbolic' if vertical else 'go-next-symbolic',
                                  tooltip_text=_('向下滚动') if vertical else _('向右滚动'))
        for button in (self.back, self.forward):
            button.add_css_class('circular')
            button.add_css_class('osd')
            if vertical:
                button.set_halign(Gtk.Align.CENTER)
                button.set_margin_top(8)
                button.set_margin_bottom(8)
            else:
                button.set_valign(Gtk.Align.CENTER)
                button.set_margin_start(8)
                button.set_margin_end(8)
            self.add_overlay(button)
        if vertical:
            self.back.set_valign(Gtk.Align.START)
            self.forward.set_valign(Gtk.Align.END)
        else:
            self.back.set_halign(Gtk.Align.START)
            self.forward.set_halign(Gtk.Align.END)
        self.back.connect('clicked', lambda *_: self.move(-1))
        self.forward.connect('clicked', lambda *_: self.move(1))
        self.adjustment.connect('changed', self.update_arrows)
        self.adjustment.connect('value-changed', self.update_arrows)
        self.animation = None
        if not vertical:
            wheel = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.BOTH_AXES)
            wheel.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            wheel.connect('scroll', self.wheel)
            self.add_controller(wheel)
        keys = Gtk.EventControllerKey()
        keys.connect('key-pressed', self.key_pressed)
        self.add_controller(keys)
        self.set_focusable(True)
        self.update_arrows()

    def update_arrows(self, *_):
        adj = self.adjustment
        last = max(adj.get_lower(), adj.get_upper() - adj.get_page_size())
        self.back.set_visible(adj.get_value() > adj.get_lower() + 1)
        self.forward.set_visible(adj.get_value() < last - 1)

    def set_value(self, value):
        adj = self.adjustment
        adj.set_value(max(adj.get_lower(), min(value, max(adj.get_lower(), adj.get_upper() - adj.get_page_size()))))

    def stop_animation(self):
        if self.animation is not None:
            self.remove_tick_callback(self.animation)
            self.animation = None

    def move(self, direction):
        self.stop_animation()
        adj = self.adjustment
        start = adj.get_value()
        target = max(adj.get_lower(), min(start + direction * max(adj.get_page_size() * .8, 100),
                                          max(adj.get_lower(), adj.get_upper() - adj.get_page_size())))
        if not self.get_settings().get_property('gtk-enable-animations'):
            self.set_value(target)
            return
        started = GLib.get_monotonic_time()

        def tick(widget, clock):
            progress = min((GLib.get_monotonic_time() - started) / 180000, 1)
            self.set_value(start + (target - start) * (1 - (1 - progress) ** 3))
            if progress >= 1:
                self.animation = None
                return False
            return True
        self.animation = self.add_tick_callback(tick)

    def wheel(self, controller, dx, dy):
        self.stop_animation()
        old = self.adjustment.get_value()
        self.set_value(old + (dx if dx else dy) * 60)
        return self.adjustment.get_value() != old

    def key_pressed(self, controller, key, keycode, state):
        backward = Gdk.KEY_Up if self.vertical else Gdk.KEY_Left
        forward = Gdk.KEY_Down if self.vertical else Gdk.KEY_Right
        if key in (backward, forward):
            self.move(-1 if key == backward else 1)
            return True
        return False
