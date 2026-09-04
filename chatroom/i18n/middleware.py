from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from chatroom.i18n.translator import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lang = self._resolve_language(request)
        request.state.lang = lang          # stash it on the request so dependencies can read it later

        response = await call_next(request)
        response.headers["Content-Language"] = lang   # helpful for debugging / API consumers
        return response

    def _resolve_language(self, request: Request) -> str:
        # 1. Explicit query param wins if present: ?lang=fa
        query_lang = request.query_params.get("lang")
        if query_lang and query_lang in SUPPORTED_LANGUAGES:
            return query_lang

        # 2. Otherwise, check if we remembered a choice from an earlier request
        cookie_lang = request.cookies.get("lang")
        if cookie_lang and cookie_lang in SUPPORTED_LANGUAGES:
            return cookie_lang

        # 3. Otherwise, fall back to the browser's Accept-Language header
        accept_language = request.headers.get("accept-language")
        if accept_language:
            for lang, _q in self._parse_accept_language(accept_language):
                short_code = lang.split("-")[0].lower()
                if short_code in SUPPORTED_LANGUAGES:
                    return short_code

        # 4. Nothing matched -> default
        return DEFAULT_LANGUAGE

    @staticmethod
    def _parse_accept_language(header: str) -> list[tuple[str, float]]:
        """
        Parses a header like: "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"
        into a list sorted by preference (q value), highest first.
        """
        languages = []
        for part in header.split(","):
            part = part.strip()
            if ";q=" in part:
                lang, q_str = part.split(";q=")
                try:
                    q = float(q_str)
                except ValueError:
                    q = 1.0
            else:
                lang, q = part, 1.0
            languages.append((lang, q))
        return sorted(languages, key=lambda pair: pair[1], reverse=True)