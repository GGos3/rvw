"""Candidate metadata for the live ADR-007 adjudication reproduction."""

GENUINE_INPUT_KEY = "genuine-input-forwarding"
GENUINE_CATCH_KEY = "genuine-hidden-failure"
FABRICATED_AWAIT_KEY = "fabricated-missing-await"

CANDIDATES = (
    {
        "key": GENUINE_INPUT_KEY,
        "rule_id": "unscoped/contract",
        "line": 8,
        "body": (
            "The public input fields `limit`, `cursor`, `fields`, and `locale` are silently "
            "dropped: the upstream query forwards only `pageNo`."
        ),
    },
    {
        "key": GENUINE_CATCH_KEY,
        "rule_id": "unscoped/correctness",
        "line": 14,
        "body": (
            "The catch block hides mapping or normalization failures by returning "
            "`{ok: true, orders: [], total: 0}`."
        ),
    },
    {
        "key": FABRICATED_AWAIT_KEY,
        "rule_id": "unscoped/correctness",
        "line": 8,
        "body": (
            "The upstream fetch at line 8 is missing `await`, so the response is a pending Promise."
        ),
    },
)
