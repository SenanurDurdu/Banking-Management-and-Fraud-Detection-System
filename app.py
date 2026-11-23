from core import ctk, create_initial_admin
from ui import App
from credit_cards import CreditCardsMixin


if __name__ == "__main__":

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    create_initial_admin()

    try:
        created = CreditCardsMixin.generate_pending_statements()

        print(
            f"Automatic statement check completed. "
            f"Created: {created}"
        )

    except Exception as error:
        print(
            f"Automatic statement generation failed: {error}"
        )

    app = App()
    app.mainloop()