"""rvw package layout.

The command surface lives in ``cli`` and wire models in ``schema``. Registry,
lane, target, hunks, dispatch, and runtimes modules implement review planning
and execution. Architectural decisions are recorded in ``DECISIONS.md``.
"""

from rvw._version import __version__

__all__: list[str] = ["__version__"]
