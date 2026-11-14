# Production wire fixtures

Candidate schema1 DTO JSON Schema, fixed synthetic positive and negative examples for the future native Rust
and TypeScript adapters. Independent acceptance is required before freeze or ORCH05. No native authorization, media, credentials or account receipts are
contained here. The examples include synthetic target pins; they do not prove an App recording.

From the repository root, check with:

```sh
PYTHONPATH=modules/content-creation python -B -m production_artifacts.schema
python -B -m pytest tests/content_creation/test_production_artifacts.py -k wire_fixtures -p no:cacheprovider
```

After a reviewed model change, `production_artifacts.schema --write` regenerates schema.json;
update roundtrip.json and negative.json with matching reviewed synthetic examples. Every consumer must reject the negative cases without coercing their scalar types or ignoring unused editing fields. Strict unknown-field/version
and snake_case rules apply identically to local and any future opt-in DigitalOcean batch
launcher. There is no network service or separate cloud schema.

Video requires measured positive integer sar_num/sar_den (1..65535); decoded-frame SAR
determines exact derived DAR = width*sar_num/(height*sar_den). Unknown/zero/missing/float/
boolean/string aspect values reject. A standalone Video positive fixture is anamorphic;
negative aspect fixtures apply to native consumers too. Old unmeasured candidate records
are not silently assumed square. The ABI remains unfrozen pending independent review.
