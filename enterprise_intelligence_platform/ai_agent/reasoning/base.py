"""Shared utilities for all reasoning layers.

No domain knowledge here. Only JSON parsing helpers that every layer needs.
No Frappe imports. No database access.
"""
from __future__ import annotations

import json
import re
from typing import Any


class BaseReasoningLayer:
    """Marker base class providing JSON parsing utilities.

    Each layer is independently callable and has no knowledge of other layers.

    ``used_fallback`` is set to True by R1–R3 when the LLM path was unavailable
    or produced unparseable output.  The ReasoningAgent reads it to populate
    ``RecommendationPackage.fallback_used``.
    """

    used_fallback: bool = False  # overridden per instance during execute()

    @staticmethod
    def _try_parse_json(text: str) -> dict[str, Any] | list[Any] | None:
        """Try to extract a JSON object or array from raw LLM text.

        Handles:
          - plain JSON,
          - JSON wrapped in markdown code fences,
          - JSON embedded inside surrounding prose.
        Returns None on any parse failure so callers can fall back deterministically.
        """
        # 1. Direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        # 2. Extract from markdown code fence  ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\[{][\s\S]*?[\]}])\s*```", text)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except (json.JSONDecodeError, ValueError):
                pass

        # 3. Extract the first JSON array or object found in the text
        bare_match = re.search(r"([\[{][\s\S]*[\]}])", text)
        if bare_match:
            try:
                return json.loads(bare_match.group(1))
            except (json.JSONDecodeError, ValueError):
                pass

        return None


__all__ = ["BaseReasoningLayer"]
