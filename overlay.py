import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo
import math

class OverlayWindow(Gtk.Window):
    def __init__(self, stop_callback, get_volume_callback=None):
        super().__init__(title="VoiceDrop Overlay")
        self.stop_callback = stop_callback
        self.get_volume_callback = get_volume_callback

        # Configure window: borderless, keep on top, skip taskbar
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_accept_focus(False)

        # Enable alpha channel for transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.set_app_paintable(True)
        self.connect("draw", self.on_draw)

        # Click anywhere on the dot to stop recording
        event_box = Gtk.EventBox()
        event_box.set_visible_window(False)
        event_box.connect("button-press-event", self.on_click)
        self.add(event_box)

        # Dimensions: ~0.5cm at 96 DPI ≈ 19px. Using 20x20 window, 14px dot.
        self.width = 20
        self.height = 20
        self.set_default_size(self.width, self.height)
        self.position_window()

        self.state = "listening"  # "listening" or "processing"
        self.processing_angle = 0.0

        # Animation timer only needed for processing spinner rotation
        self.animation_timer = GLib.timeout_add(33, self.on_animation_tick)

    def position_window(self):
        """Position the dot near the bottom-center of the screen, close to the edge."""
        display = Gdk.Display.get_default()
        monitor = display.get_monitor(0)
        if monitor:
            geom = monitor.get_geometry()
            x = geom.x + (geom.width - self.width) // 2
            # 18 pixels offset from the bottom of the screen — much lower than before
            y = geom.y + geom.height - self.height - 18
            self.move(x, y)

    def set_state(self, state):
        self.state = state
        self.queue_draw()

    def on_click(self, widget, event):
        if event.button == 1:  # Left click
            self.stop_callback()
            return True
        return False

    def on_animation_tick(self):
        if self.state == "processing":
            self.processing_angle += 0.15
        self.queue_draw()
        return True

    def on_draw(self, widget, cr):
        """Draw a plain small dot. Blue = listening, purple spinner = processing. No text, no panel."""
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)  # fully transparent background
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        cx = self.width / 2
        cy = self.height / 2
        r = 7.0  # ~14px diameter dot

        if self.state == "listening":
            cr.set_source_rgba(0.22, 0.74, 0.97, 0.9)  # solid blue
            cr.arc(cx, cy, r, 0, 2 * math.pi)
            cr.fill()
        else:  # processing
            # faint ring
            cr.set_source_rgba(0.65, 0.55, 0.98, 0.25)
            cr.set_line_width(2.5)
            cr.arc(cx, cy, r, 0, 2 * math.pi)
            cr.stroke()
            # spinning arc segment
            cr.set_source_rgba(0.65, 0.55, 0.98, 1.0)
            cr.arc(cx, cy, r, self.processing_angle, self.processing_angle + math.pi * 0.75)
            cr.stroke()

        cr.restore()
        return False

    def close_window(self):
        GLib.source_remove(self.animation_timer)
        self.destroy()
        Gtk.main_quit()
