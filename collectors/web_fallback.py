class DisabledWebFallback:
    """Tier-5 boundary. Deliberately disabled as a core price feed."""

    source_tier = 5

    def fetch(self, *args, **kwargs):
        raise RuntimeError("Web scraping fallback is disabled; enable only with explicit source governance")
