<div align="center">

# SocialGravity ledger anchors

**A public witness against our own future selves.**

Mirrored head hashes of SocialGravity's append-only identity licensing ledger, committed where
we cannot quietly rewrite them.

[![Log](https://img.shields.io/badge/log-RFC%206962-20231C?style=flat-square)](https://github.com/socialgravity/receipts/blob/main/docs/transparency-log-audit.md)
[![Timestamps](https://img.shields.io/badge/timestamps-RFC%203161-6B705C?style=flat-square)](https://github.com/socialgravity/receipts/blob/main/docs/receipt-spec-v1.md)
[![Force push](https://img.shields.io/badge/force%20push-blocked-6B705C?style=flat-square)](#what-this-does-and-does-not-prove)
[![Data](https://img.shields.io/badge/data-CC0%201.0-6B705C?style=flat-square)](LICENSE)

[Verifier](https://github.com/socialgravity/receipts) ·
[Audit guide](https://github.com/socialgravity/receipts/blob/main/docs/transparency-log-audit.md) ·
[Latest head](latest.json)

</div>

---

Our ledger is a transparency log (RFC 6962). Its signed tree heads are already anchored with an
independent RFC 3161 timestamp authority. This repository is the second, independent witness:
each new head is committed here, so the record of what our ledger said, and when, is held on
infrastructure whose clock we do not control and whose history we cannot silently edit.

The published verifier uses it. Its `witnessed head` check holds the live log against what we
published here:

```text
  PASS           witnessed head
                 the live tree equals the publicly witnessed head (size 56) byte for byte
```

## How the mirror runs

Hourly, from a [GitHub Actions workflow](.github/workflows/mirror.yml) in this repository. It
reads the public tree head endpoint and commits with the workflow's own token, so it holds no
SocialGravity credential: a witness that depends on a long-lived secret belonging to the party
being witnessed is a weaker witness.

It writes nothing rather than writing something it cannot stand behind. Before committing a head
it checks the Ed25519 signature against the key pinned in
[socialgravity/receipts](https://github.com/socialgravity/receipts/blob/main/verifier/lib/keys.ts),
and it insists that every field it publishes matches the copy inside the signed bytes, because
the endpoint repeats some of them outside the signature and an outer field that disagrees with
the signed one is exactly how a doctored root would sneak in. The refusals are listed in
[`scripts/mirror_head.py`](scripts/mirror_head.py).

Each file says what it stands on. An RFC 3161 timestamp is stronger evidence than a git commit,
but the anchoring job trails the live tree, so `anchor` carries the timestamp only when it covers
that exact tree, and `anchor_note` says which of the two the file rests on. A head with no stamp
of its own gets pinned once a later anchored head proves it by consistency.

This starts at head 56. Head 30 was placed by hand while the mirror was being built, and GitHub's
scheduler is best effort, so the file dates are the record of cadence rather than this sentence.

Check the live head yourself at any time:

```sh
curl -s "https://id.socialgravity.ai/functions/v1/idl-log-sth" | jq .data.sth
```

## What one anchor file contains

`anchors/head-<seq>.json`, one file per ledger head, append-only:

- `tree_size`, `root_hash`: the RFC 6962 Merkle root over the ledger's entry hashes
- `sth_signed_at`, `sth_signature`: the Ed25519-signed tree head exactly as the API served it,
  including the canonical bytes recipe, so the file is self-authenticating
- `anchor`: the anchor block the API reported at mirror time, when present
- [`latest.json`](latest.json) points at the newest file

## How to use this against us

1. Pick any anchor file. Verify the Ed25519 signature over its `canonical_json` against the
   pinned public key in
   [socialgravity/receipts](https://github.com/socialgravity/receipts/blob/main/verifier/lib/keys.ts).
2. Fetch the live log: `https://id.socialgravity.ai/functions/v1/idl-log-sth?leaves=1` and
   recompute the root for that `tree_size` yourself. It must equal `root_hash`.
3. The commit that added the file is GitHub's record that this root existed no later than the
   commit time. If the live log ever shows a different root for the same tree size, or a later
   tree that is not an append of this one (a consistency proof will refuse), you have caught us
   rewriting history, and this repository is the evidence.

The verifier and the
[audit guide](https://github.com/socialgravity/receipts/blob/main/docs/transparency-log-audit.md)
automate the arithmetic.

## What this does and does not prove

A mirrored head proves the ledger's state existed no later than the commit time, and makes any
later rewrite of that state detectable. It does not date anything before the first anchor here
(2026-07-30), and it does not prove the ledger's contents are true, only that they have not been
changed after the fact. What is deliberately outside the ledger is listed in the receipts repo's
audit guide.

Force pushes and branch deletion are disabled on this repository's default branch, with
administrators included, so rewriting it would require visibly turning that protection off. If
this history ever changes anyway, treat it as a finding, not housekeeping.

## Licence

The anchor data is released under [CC0 1.0](LICENSE). Copy it, mirror it, keep your own archive
of it. A witness is more useful the more places it exists, and asking for attribution before you
can hold us to our own hashes would be silly.
