import os
from babel.messages.pofile import read_po
from babel.messages.mofile import write_mo

LOCALES_DIR = "locales"

def compile_all():
    for lang in os.listdir(LOCALES_DIR):
        po_path = os.path.join(LOCALES_DIR, lang, "LC_MESSAGES", "messages.po")
        mo_path = os.path.join(LOCALES_DIR, lang, "LC_MESSAGES", "messages.mo")
        if os.path.exists(po_path):
            with open(po_path, "rb") as po_file:
                catalog = read_po(po_file, locale=lang)
            with open(mo_path, "wb") as mo_file:
                write_mo(mo_file, catalog)
            print(f"Compiled {po_path} -> {mo_path}")

if __name__ == "__main__":
    compile_all()