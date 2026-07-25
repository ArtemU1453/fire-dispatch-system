"""Rules infrastructure.

A universal system for storing, versioning and evaluating normatives in the
database. Algorithms never embed normatives: they pass an input context to the
Rule Engine and receive ready-made requirements, constraints, minimum and
recommended compositions, and required capabilities. Changing a norm means
updating database records — no code change.

Built on the Stage-2 data model without altering it. This stage builds only the
rules infrastructure — it performs no resource selection, routing or AI.
"""
