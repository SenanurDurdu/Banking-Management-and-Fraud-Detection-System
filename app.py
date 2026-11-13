
from core import ctk, create_initial_admin
from ui import App


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    create_initial_admin()

    app = App()
    app.mainloop()
