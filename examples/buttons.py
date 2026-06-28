"""buttons.py - An example which creates and implements four image buttons."""

import tkinter as tk
from imagelist import ImageList


class DemoForm(tk.Frame):
    """The image buttons demo window."""

    def __init__(self, master):
        """Construct the image buttons demo window."""
        super().__init__(master, bd=3, relief='ridge', padx=20, pady=20)
        self.grid()

        group = tk.LabelFrame(self, text='Image Buttons')
        image_list = ImageList('image_folder', (32, 32), True)
        image_width, image_height = image_list.image_size
        for i, name in enumerate(['printer', 'settings', 'help', 'stop']):

            def handler(index=image_list.index_of_key(name)):
                text = '???' if index < 0 else image_list.keys[index].title()
                label.configure(text=f"'{text}' Button")

            button = tk.Button(group, image=image_list[name], command=handler)
            button.configure(width=image_width + 8, height=image_height + 8)
            button.grid(column=i, row=0, padx=15, pady=(10, 15))
        group.grid(pady=(0, 20))

        label = tk.Label(self, bd=1, relief='solid', width=20, anchor='center')
        label.configure(text='Click any Button')
        label.grid()


if __name__ == '__main__':
    main_form = DemoForm(tk.Tk())
    main_form.mainloop()
