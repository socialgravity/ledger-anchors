# SocialGravity ledger anchors

Mirrored head hashes of SocialGravity's append-only identity licensing ledger.

Our ledger is a transparency log (RFC 6962). Its signed tree heads are already anchored with
an independent RFC 3161 timestamp authority. This repository is the second, independent
witness: each new head is committed here, so the record of what our ledger said, and when,
is held on infrastructure we do not control the clock of and cannot quietly rewrite.

**Current status, stated plainly because a witness that overclaims is worse than no witness.**
This repository holds a manual seed at head 30 only. The automated mirror (`idl-ledger-anchor`)
is written but not yet enabled, so heads are NOT arriving hourly yet and the ledger is already
ahead of what you see here. Read the gap between the newest file below and the live head as
exactly what it is: this witness is not live yet. When the job is enabled this note goes, and
the file dates themselves become the evidence of the cadence rather than this sentence.

## What one anchor file contains

`anchors/head-<seq>.json`, one file per ledger head, append-only:

- `tree_size`, `root_hash`: the RFC 6962 Merkle root over the ledger's entry hashes
- `sth_signed_at`, `sth_signature`: the Ed25519-signed tree head exactly as the API served it,
  including the canonical bytes recipe, so the file is self-authenticating
- `anchor`: the anchor block the API reported at mirror time, when present
- `latest.json` points at the newest file

## How to use this against us

1. Pick any anchor file. Verify the Ed25519 signature over its `canonical_json` against the
   pinned public key in
   [socialgravity/receipts](https://github.com/socialgravity/receipts)`/verifier/lib/keys.ts`.
2. Fetch the live log: `https://id.socialgravity.ai/functions/v1/idl-log-sth?leaves=1` and
   recompute the root for that `tree_size` yourself. It must equal `root_hash`.
3. The commit that added the file is GitHub's record that this root existed no later than the
   commit time. If the live log ever shows a different root for the same tree size, or a
   later tree that is not an append of this one (a consistency proof will refuse), you have
   caught us rewriting history, and this repository is the evidence.

The verifier and the audit guide in
[socialgravity/receipts](https://github.com/socialgravity/receipts) automate the arithmetic.

## What this does and does not prove

A mirrored head proves the ledger's state existed no later than the commit time, and makes
any later rewrite of that state detectable. It does not date anything before the first
anchor here (2026-07-30), and it does not prove the ledger's contents are true, only that
they have not been changed after the fact. What is deliberately outside the ledger is listed
in the receipts repo's transparency-log audit guide.

Force pushes are disabled on this repository's default branch. If its history ever changes
anyway, treat that as a finding, not housekeeping.
