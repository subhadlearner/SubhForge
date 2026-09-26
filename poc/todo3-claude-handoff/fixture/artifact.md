# Proposed authorization flow

1. Ask the authorization service whether the request is allowed.
2. For an explicit denial, emit an audit event containing request ID and
   reason code, then deny the request.
3. For a timeout, deny the request immediately and skip the audit call to
   minimize latency.
