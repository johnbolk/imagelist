"""mac_button.py - An example of a macOS compatible image button widget."""

import platform
import tkinter as tk
from imagelist import ImageList


class MacButton(tk.Button):
    """A macOS compatible image button widget."""

    def __init__(self, parent, image_list, image_id, command):
        """Create and initialize the macOS compatible image button widget."""
        self._grayed = self._image = image_list[image_id]
        if platform.system() == 'Darwin':  # Check for the macOS platform
            self._grayed = image_list.grayed[image_id]
        width, height = image_list.image_size
        super().__init__(parent, image=self._image, command=command)
        self.config(width=width * 1.25, height=height * 1.25)

    @property
    def enabled(self):
        """Get/Set the button enabled status."""
        return self['state'] != tk.DISABLED

    @enabled.setter
    def enabled(self, enabled):
        """Get/Set the button enabled status."""
        self['state'] = tk.NORMAL if enabled else tk.DISABLED
        self['image'] = self._image if enabled else self._grayed


class DemoForm(tk.Frame):
    """The MacButton demo window."""

    def __init__(self, master):
        """Construct the MacButton demo window."""
        super().__init__(master, bd=3, relief='ridge', padx=50, pady=20)
        self.grid()

        image_list = ImageList(image_size=(48, 48))
        image_list.add('image_folder/printer.png')  # Add an image of a printer
        self._button = MacButton(self, image_list, 0, self._on_print)
        self._button.enabled = False
        self._button.grid(pady=20)

        self._print_enable = tk.IntVar()
        checkbox = tk.Checkbutton(self, text='Enable Print Button')
        checkbox.config(variable=self._print_enable, command=self._on_check)
        checkbox.grid()

    def _on_check(self):
        """Event handler for the Checkbutton."""
        self._button.enabled = self._print_enable.get() != 0

    @staticmethod
    def _on_print():
        """Event handler for the MacButton."""
        print('*** Print ***')


if __name__ == '__main__':
    main_form = DemoForm(tk.Tk())
    main_form.mainloop()
