import time
import math
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio, Gdk


class TimerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.TimerApp")
        self.window = None
        self.seconds_left = 0
        self.running = False
        self.start_time = None
        self.timeout_id = None
        self.connect(
            "activate", self.do_activate
        )  # Explicitly connect to the 'activate' signal

    def do_activate(self, *args):  # Ensure that 'do_activate' is called correctly
        if not self.window:
            self.window = Gtk.ApplicationWindow(application=self)
            self.window.set_title("Countdown Timer")
            self.window.set_default_size(400, 300)

            # Main layout
            grid = Gtk.Grid(
                column_spacing=10, row_spacing=10, hexpand=True, vexpand=True
            )
            self.window.set_child(grid)

            # Timer label
            self.timer_label = Gtk.Label(label="00:00:00")
            grid.attach(self.timer_label, 0, 0, 3, 1)

            # Entry fields
            self.hours_entry = self.create_entry("0")
            self.minutes_entry = self.create_entry("1")
            self.seconds_entry = self.create_entry("0")

            grid.attach(self.hours_entry, 0, 1, 1, 1)
            grid.attach(self.minutes_entry, 1, 1, 1, 1)
            grid.attach(self.seconds_entry, 2, 1, 1, 1)

            # Buttons
            self.start_button = Gtk.Button(label="Start")
            self.start_button.connect("clicked", self.start_timer)

            self.pause_button = Gtk.Button(label="Pause")
            self.pause_button.connect("clicked", self.pause_timer)

            self.stop_button = Gtk.Button(label="Stop")
            self.stop_button.connect("clicked", self.stop_timer)

            grid.attach(self.start_button, 0, 2, 1, 1)
            grid.attach(self.pause_button, 1, 2, 1, 1)
            grid.attach(self.stop_button, 2, 2, 1, 1)

            # Circular progress indicator
            self.drawing_area = Gtk.DrawingArea()
            self.drawing_area.set_content_width(200)
            self.drawing_area.set_content_height(200)
            self.drawing_area.set_draw_func(self.on_snapshot)
            grid.attach(self.drawing_area, 0, 3, 3, 1)

            # Add system tray menu
            self.setup_system_tray()

        self.window.show()  # Make sure this is called at the end of do_activate

    def create_entry(self, default_text):
        entry = Gtk.Entry()
        entry.set_text(default_text)
        entry.set_width_chars(3)
        return entry

    def setup_system_tray(self):
        # Create actions for the system tray menu
        about_action = Gio.SimpleAction.new("about", None)
        quit_action = Gio.SimpleAction.new("quit", None)

        # Connect the actions to their respective methods
        about_action.connect("activate", self.show_about)
        quit_action.connect("activate", self.quit_app)

        # Add actions to the application
        self.add_action(about_action)
        self.add_action(quit_action)

        # Create the system tray menu using Gtk.Popover
        self.popover = Gtk.Popover()

        # Create a VBox to hold the menu items
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Create "About" and "Quit" menu buttons
        about_item = Gtk.Button(label="About")
        about_item.connect("clicked", self.show_about)
        menu_box.append(about_item)

        quit_item = Gtk.Button(label="Quit")
        quit_item.connect("clicked", self.quit_app)
        menu_box.append(quit_item)

        # Set the content of the popover
        self.popover.set_child(menu_box)

        # Create a button to trigger the popover
        tray_button = Gtk.Button(label="Show Tray Menu")
        tray_button.connect("clicked", self.show_tray_menu)
        grid.attach(
            tray_button, 0, 4, 3, 1
        )  # Attach the button at the bottom of the grid

    def show_tray_menu(self, widget):
        # Show the popover at the button's position
        self.popover.popup_at_pointer(None)

    def show_about(self, action, parameter):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("Timekeeper")
        about_dialog.set_version("1.0.0")
        about_dialog.set_license_type(Gtk.License.MIT)
        about_dialog.set_authors(["Stefano Scansani"])
        about_dialog.set_transient_for(self.window)
        about_dialog.show()

    def quit_app(self, action, parameter):
        self.quit()

    def start_timer(self, widget):
        try:
            hours = int(self.hours_entry.get_text())
            minutes = int(self.minutes_entry.get_text())
            seconds = int(self.seconds_entry.get_text())
            self.seconds_left = (hours * 3600) + (minutes * 60) + seconds
            self.start_time = time.time()
            self.running = True
            self.timer_label.set_text(f"{hours:02}:{minutes:02}:{seconds:02}")
            if self.timeout_id is None:
                self.timeout_id = GLib.timeout_add_seconds(1, self.update_timer)
        except ValueError:
            return  # Handle invalid input gracefully

    def update_timer(self):
        if self.running and self.seconds_left > 0:
            elapsed_time = time.time() - self.start_time
            remaining_time = self.seconds_left - int(elapsed_time)
            if remaining_time <= 0:
                self.running = False
                remaining_time = 0
                self.timer_label.set_text("Time's up!")

            self.timer_label.set_text(
                f"{remaining_time // 3600:02}:{(remaining_time % 3600) // 60:02}:{remaining_time % 60:02}"
            )
            self.drawing_area.queue_draw()  # GTK 3
            self.drawing_area.queue_resize()  # GTK 4 requires explicit resize calls sometimes.

            return True  # Continue the timer update
        return False  # Stop the timer after completion

    def pause_timer(self, widget):
        self.running = False

    def stop_timer(self, widget):
        self.running = False
        self.seconds_left = 0
        self.timer_label.set_text("00:00:00")
        self.drawing_area.queue_draw()

    def on_snapshot(self, widget, ctx, width, height):
        """Draw the circular progress (filled pie-like)."""
        radius = min(width, height) // 2 - 10  # Adjust the margin

        # Background circle (light gray)
        ctx.set_source_rgba(
            0.9, 0.9, 0.9, 0.1
        )  # Light gray background color with transparency
        ctx.arc(width // 2, height // 2, radius, 0, 2 * math.pi)
        ctx.fill()

        if self.running and self.seconds_left > 0:
            elapsed_time = time.time() - self.start_time
            remaining_time = self.seconds_left - int(elapsed_time)
            if remaining_time < 0:
                remaining_time = 0
            progress_angle = (remaining_time / self.seconds_left) * 2 * math.pi

            # Progress fill (green color)
            ctx.set_source_rgba(0.6, 0.5, 0.2, 0.5)  # Green for the progress

            # Draw the full circle and the progress as a filled sector
            ctx.move_to(width // 2, height // 2)  # Move to center
            ctx.arc(
                width // 2,
                height // 2,
                radius,
                -math.pi / 2,
                -math.pi / 2 + progress_angle,
            )  # Draw the arc
            ctx.line_to(width // 2, height // 2)  # Close the path to the center
            ctx.fill()  # Fill the sector with the green color

        # Optionally, you can add a border around the entire circle
        ctx.set_source_rgba(0, 0, 0, 0.1)  # Black color for the border
        ctx.set_line_width(1)  # Thickness of the border
        ctx.arc(
            width // 2, height // 2, radius, 0, 2 * math.pi
        )  # Outline the full circle
        ctx.stroke()


if __name__ == "__main__":
    app = TimerApp()
    app.run()
