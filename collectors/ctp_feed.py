from __future__ import annotations

import os


class CTPFeed:
    """Credential-safe CTP boundary. Vendor SDK integration belongs behind this API."""

    REQUIRED = ("CTP_BROKER_ID", "CTP_USER_ID", "CTP_PASSWORD", "CTP_MD_FRONT")

    def configured(self) -> bool:
        return all(os.getenv(k) for k in self.REQUIRED)

    def connect(self) -> None:
        if not self.configured():
            missing = [k for k in self.REQUIRED if not os.getenv(k)]
            raise RuntimeError(f"CTP is not configured; missing: {', '.join(missing)}")
        raise NotImplementedError("Install the broker-approved CTP SDK before production connection")
