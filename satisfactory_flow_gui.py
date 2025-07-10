import os
import tkinter as tk
from satisfactory_flow.gui import App
from satisfactory_flow.console import ConsoleApp


def has_display() -> bool:
    if os.name == "nt":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


if __name__ == "__main__":
    if has_display():
        try:
            app = App()
            app.mainloop()
        except tk.TclError:
            print("No display available, falling back to console mode")
            ConsoleApp().run()
    else:
        print("No display detected, running in console mode")
        ConsoleApp().run()
