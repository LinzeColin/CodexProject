# Webhook bridge status

The former `repository_dispatch` webhook bridge design is retired and is not an
Automation C entry point. No Worker, connector, form, or repository workflow is
authorized by this document to receive a Task Pack or publish repository state.

The supported write boundary is the explicit external authenticated publisher
described in `RUN_APPROVED_TASKPACK.md`. It creates one marker-bound PR from an
already-pushed same-repository branch and never stores publisher credentials in
repository automation.

Reintroducing a webhook or connector requires a separate approved Task Pack
covering authentication, replay protection, payload size and schema limits,
secret storage, audit retention, rate limiting, exact SHA binding, failure
compensation, and Zero-Open settlement. Until then, treat any webhook bridge as
unsupported and fail closed.
