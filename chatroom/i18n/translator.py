import gettext
from pathlib import Path
from fastapi import Request, Depends


LOCALES_DIR = Path(__file__).resolve().parent.parent.parent / "locales"
DOMAIN = "messages"
SUPPORTED_LANGUAGES = ["en", "fa"]
DEFAULT_LANGUAGE = "en"

_translations: dict[str, gettext.NullTranslations] = {}


def load_translations() -> None:
    """Load every supported language's compiled .mo file into memory once, at startup."""
    for lang in SUPPORTED_LANGUAGES:
        try:
            translation = gettext.translation(DOMAIN, localedir=str(LOCALES_DIR), languages=[lang])
        except FileNotFoundError:
            # No .mo file found for this language yet (forgot to compile, or new language not translated).
            # Falls back to a "null" translator that just returns the original text unchanged.
            translation = gettext.NullTranslations()
        _translations[lang] = translation


def get_translator(lang: str):
    """Return a callable: _('some text') -> translated text, for the given language."""
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    translation = _translations.get(lang, gettext.NullTranslations())
    return translation.gettext

def get_language(request: Request) -> str:
    """Dependency: read the language that the middleware already resolved for this request."""
    return getattr(request.state, "lang", DEFAULT_LANGUAGE)


def get_translator_dep(lang: str = Depends(get_language)):
    """Dependency: returns a ready-to-use translator function for the current request's language."""
    return get_translator(lang)