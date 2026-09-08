from __future__ import annotations

import os


class RealtimeWebSocketFeed:
    def configured(self) -> bool:
        return bool(os.getenv("REALTIME_API_URL") and os.getenv("REALTIME_API_TOKEN"))

    async def stream(self):
        if not self.configured():
            raise RuntimeError("REALTIME_API_URL and REALTIME_API_TOKEN are required")
        raise NotImplementedError("Implement vendor-specific authentication and message mapping here")
