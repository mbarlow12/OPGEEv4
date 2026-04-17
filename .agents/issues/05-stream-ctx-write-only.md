# `Stream.ctx` is a write-only attribute

**Severity:** Important
**Location:** `opgee/stream.py:61, 71`; assignment site `opgee/field.py:160-161`

## Problem
Stream accepts `ctx: FieldContext | None = None` and stores it; Field wires it during stream registration. But no code reads `stream.ctx` anywhere — grep confirms zero reads. The spec §3.1/§4.3 intent was for Stream to default T/P from `ctx.stp` when not supplied, but the current constructor takes `tp` directly (positional) and ctx is inert.

## Suggested fix
Either:
- Drop the `ctx` parameter from `Stream` entirely and delete the Field-side assignment; or
- Follow through on the spec: make `tp` optional, default from `ctx.stp` when absent, and document the fallback.

Current state (both present; ctx unused) is the worst of both.
