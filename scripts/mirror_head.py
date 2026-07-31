#!/usr/bin/env python3
"""Mirror the current anchored ledger head into this repository.

This runs from a GitHub Actions schedule and fetches only the public signed tree head
endpoint. It holds no credentials of ours: the write is done with the workflow's own
GITHUB_TOKEN, scoped to this repository. That is deliberate. A witness that needs a
long-lived token belonging to the party being witnessed is a weaker witness.

Refusals, all of which exit 0 and write nothing, because a missing file is honest and a
wrong file is not:

  * the endpoint does not answer ok=true on contract_version 1
  * the Ed25519 signature over the head does not verify against the pinned key
  * a field repeated outside the signature disagrees with the signed copy of it
  * the file for this head already exists, which makes re-running a no-op

The document shape matches the manual seed at head 30 and the platform's own
_shared/anchorMirror.ts writer, so whichever producer gets to a head first, the file for
that head is complete and self-authenticating on its own.
"""

import base64
import json
import os
import sys
import urllib.request

STH_URL = "https://id.socialgravity.ai/functions/v1/idl-log-sth"

# Pinned, exactly as in socialgravity/receipts verifier/lib/keys.ts. Never read the key
# from the response we are checking.
PINNED_SPKI_B64 = "MCowBQYDK2VwAyEAXzTD6OwOCWzDk9K4zLoOeHSpGTO+b25SNUvkmqmqRE4="


def skip(reason: str) -> None:
    print(f"nothing mirrored: {reason}")
    sys.exit(0)


def fail(reason: str) -> None:
    print(f"::error::{reason}")
    sys.exit(1)


def fetch_sth() -> dict:
    # The endpoint sets no-store, but a cache buster costs nothing and a stale mirrored
    # head is exactly the failure this repository exists to make visible.
    req = urllib.request.Request(
        f"{STH_URL}?mirror=1",
        headers={"accept": "application/json", "user-agent": "socialgravity-ledger-anchors-mirror"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def verify_signature(canonical_json: str, sig_b64: str) -> bool:
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    from cryptography.exceptions import InvalidSignature

    key = load_der_public_key(base64.b64decode(PINNED_SPKI_B64))
    try:
        key.verify(base64.b64decode(sig_b64), canonical_json.encode("utf-8"))
        return True
    except InvalidSignature:
        return False


def main() -> None:
    body = fetch_sth()
    if not body.get("ok") or body.get("contract_version") != 1:
        fail(f"unexpected envelope: ok={body.get('ok')} contract_version={body.get('contract_version')}")

    sth = body.get("data", {}).get("sth") or {}
    signature = sth.get("signature") or {}
    anchor = sth.get("anchor")

    tree_size = str(sth.get("tree_size", ""))
    root_hash = sth.get("root_hash")
    if not tree_size or not root_hash:
        fail("response carried no tree head")

    # An external RFC 3161 stamp is better evidence than a git commit, but waiting for one
    # before mirroring anything is stricter than the evidence requires and it costs coverage:
    # the anchor job trails the live tree, so insisting the two match meant writing nothing on
    # most ticks. A head witnessed only by the commit is still witnessed, because the commit
    # time is GitHub's record and not ours. So mirror every head, and say exactly which kind
    # of evidence this file carries.
    #
    # The anchor block is only included when it covers THIS tree. An anchor for an earlier
    # head sitting in a file about a later one would read as a timestamp on something it
    # never stamped.
    anchor_covers_this_head = bool(anchor) and str(anchor.get("head_seq", "")) == tree_size
    if anchor_covers_this_head:
        anchor_note = "externally timestamped by an RFC 3161 authority, see anchor.external_receipt"
    elif anchor:
        anchor_note = (
            f"no external timestamp for this head yet: the newest one covers head "
            f"{anchor.get('head_seq')}. The commit that added this file is the time evidence "
            "until a later anchored head proves this one by consistency."
        )
    else:
        anchor_note = (
            "no external timestamp for this head. The commit that added this file is the "
            "time evidence."
        )

    head_seq = tree_size

    canonical = signature.get("canonical_json")
    sig_b64 = signature.get("sig_base64")
    if not canonical or not sig_b64:
        fail("head carried no signature to check")
    if not verify_signature(canonical, sig_b64):
        fail(f"head {head_seq} does not verify against the pinned key, refusing to mirror it")

    # Everything we publish has to come from inside the signed bytes. The response repeats
    # tree_size and root_hash outside the signature, and an unsigned field that disagrees
    # with the signed one is the whole game: it would let a doctored root be mirrored under
    # a signature that covers a different tree. So parse the canonical JSON, insist the
    # copies agree, and write the signed values.
    try:
        signed = json.loads(canonical)
    except json.JSONDecodeError:
        fail("signed canonical json did not parse")

    if signed.get("statement") != "transparency_log_tree_head":
        fail(f"signature covers statement {signed.get('statement')!r}, not a tree head")

    signed_tree_size = str(signed.get("tree_size", ""))
    signed_root_hash = signed.get("root_hash")
    signed_at = signed.get("signed_at")

    if signed_tree_size != tree_size:
        fail(f"tree_size disagrees with the signed head: {tree_size} outside, {signed_tree_size} inside")
    if signed_root_hash != root_hash:
        fail(f"root_hash disagrees with the signed head: {root_hash} outside, {signed_root_hash} inside")
    if sth.get("signed_at") != signed_at:
        fail(f"signed_at disagrees with the signed head: {sth.get('signed_at')} outside, {signed_at} inside")

    tree_size = signed_tree_size
    root_hash = signed_root_hash

    path = f"anchors/head-{head_seq.zfill(9)}.json"
    if os.path.exists(path):
        skip(f"{path} already exists")

    document = {
        "head_seq": head_seq,
        "tree_size": tree_size,
        "root_hash": root_hash,
        "sth_signed_at": signed_at,
        "sth_signature": signature,
        "anchor": anchor if anchor_covers_this_head else None,
        "anchor_note": anchor_note,
        "source": STH_URL,
        "mirrored_by": "github actions, .github/workflows/mirror.yml",
    }

    os.makedirs("anchors", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(document, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    with open("latest.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"head_seq": head_seq, "path": path}, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"mirrored head {head_seq}, root {root_hash[:16]}..., to {path}")

    step_output = os.environ.get("GITHUB_OUTPUT")
    if step_output:
        with open(step_output, "a", encoding="utf-8") as fh:
            fh.write("wrote=true\n")
            fh.write(f"head_seq={head_seq}\n")
            fh.write(f"root_hash={root_hash}\n")


if __name__ == "__main__":
    main()
