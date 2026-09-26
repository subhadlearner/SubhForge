# Contract: denied access must remain auditable

AC-1: Every denied access attempt must produce one audit event, including a
denial caused by an authorization service timeout. The event must contain a
request ID and a reason code. Audit delivery failure must be surfaced rather
than silently treated as a successful denial.
