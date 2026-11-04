# Maintainer schema — Python (Awesome KB)

OpenShelf 1.7, profile awesome; kb.yaml declares layout. OpenNorms/openshelf
defines the format; hexsecs/awesome-kb-skill defines the maintenance method.

## Canon

vinta/awesome-python is canon, designated by the owner's initial-pass request on
2026-11-04. Import its curated README entries, excluding badges, sponsors,
navigation and contribution boilerplate. Linked lists are not recursive.
Python bullet subgroups and Go Markdown heading hierarchy remain categories.
Repeated URLs in different categories retain their separate listed contexts.

## Ingest

Run python3 tools/ingest.py --date YYYY-MM-DD. The default input is the
immutable raw/2026-11-04 capture. Use --source for another capture directory
(README.md plus capture.json). Capture new revisions under a new dated directory;
never overwrite old raw files. Update raw/MANIFEST.sha256 for new captures.
Generate index.md and wiki/index-*.md from page metadata; do not edit by hand.

## Fields and evidence

Every new entity gets depth: stub, a random UUIDv7, and creation date of ingest.
Living resource status is unknown and last_checked is absent until verified.
Finished books use status: published. list_summary preserves the original
description; summary is plain text capped at 160 characters. Bare links get
a descriptive generated placeholder, explicitly identified in their body.
Source citations pin the upstream commit; raw captures preserve source text.
On re-ingest preserve uid, created, authored bodies (brief/full/deep), status,
verification dates, related links and extra source records.
Keep delisted pages with tombstone notes; never delete an entity.

## Gates

Run python3 tools/check.py, repeat ingest until byte-identical, then openshelf
lint . before landing. CI runs these checks. Stub freshness warnings are
expected; never invent verification dates. Content license: CC-BY-4.0.

## Generated README list

The README contains a marked generated list, maintained by tools/render_readme.py
from the same index graph. Ingest updates both views; do not edit between the
generated markers. Introduction and license sections outside the markers stay
manual. Entry names link to KB pages and upstream links open original resources.
Large catalogs continue under lists/ at category boundaries to keep README and
continuation pages below GitHub's 500 KiB display limit. These files are generated,
not additional OpenShelf entities. Run python3 tools/render_readme.py --check to
verify completeness, links, display size and synchronization.
