# Python (Awesome KB)

An [OpenShelf](https://github.com/OpenNorms/openshelf) 1.7 knowledge base
ingested from [vinta/awesome-python](https://github.com/vinta/awesome-python), part of the
[Awesome KB](https://github.com/hexsecs/awesome-kb) network.

**[Browse the knowledge base](index.md).** All entries start at stub depth.
This is an initial inventory import, not independent verification of projects.
The list remains canon. Original resource URLs, descriptions, categories and
source revision are retained. Linked lists are not recursively ingested.

## Reproduce and validate

```sh
python3 tools/ingest.py --date 2026-11-04
python3 tools/check.py
openshelf lint .
```

The immutable source capture is under raw/2026-11-04; see capture.json for
provenance and AGENTS.md for maintenance. CI checks completeness, links,
checksums, identity, idempotency, authored-depth preservation and OpenShelf lint.

## License and attribution

Content follows upstream's **CC-BY-4.0** license, reproduced in [LICENSE](LICENSE).
Original list content is attributed to [vinta/awesome-python](https://github.com/vinta/awesome-python);
this KB transforms each list entry into an OpenShelf stub and generated indexes.
Linked projects retain their own licenses. No endorsement is implied.
Source revision: [2a1a1959a3a6](https://github.com/vinta/awesome-python/tree/2a1a1959a3a6e6853ecb229b7a8deb5790367442).
