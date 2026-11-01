# Recording library

This Rust crate is the private, local recording inbox shared by Stream Extend and Creator Extend.
Stream Extend registers the finalized path OBS returns; Creator Extend reads and updates the same
metadata. Video is not copied or uploaded.

The JSON ledger is written atomically through `local-settings` and guarded by a cross-process file
lock so the two desktop apps cannot overwrite each other's updates. Only canonical, non-empty local
video files are accepted. A repeated path updates the existing record rather than creating a second
inbox item.

