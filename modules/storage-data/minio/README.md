# Pinned local MinIO builds

The default stack builds the existing MinIO server and `mc` client from upstream source.
It no longer pulls the retired `quay.io/minio/minio:latest` or `quay.io/minio/mc:latest` images.
The [recipe](Dockerfile) has `server` and `client` targets. [Provenance](provenance.json)
records full source commits, archive SHA-256 hashes and base-image manifest digests.
The existing manual bootstrap remains `scripts/setup/minio_init.sh` from the repository root.

From the repository root, with Docker Compose and the documented environment prepared:

```bash
docker compose build minio minio-bootstrap
docker compose up -d minio
docker compose --profile setup run --rm minio-bootstrap
```

First builds download Go dependencies and can take several minutes. Later starts reuse the
build cache. Source archives are checksum-verified; `go build -mod=readonly` preserves the
upstream module graph, with Go's normal dependency checksum verification. Runtime package
updates remain Debian-managed; this is not a claim of byte-identical image reproducibility.

The existing S3 endpoint, private credentials, loopback ports, named `minio-data` volume and
bucket/lifecycle commands stay the storage contract. The recipe does not delete, migrate or
change ownership of an existing volume. Back up data before updating an existing installation.
Source changes require a new reviewed commit/archive checksum and repeated live acceptance.
Do not replace the pins with `latest` to work around a failed build.

The server and client repositories are archived and MinIO's community distribution is
[source-only](https://github.com/minio/minio). The images retain their upstream license files
and provenance. This is a local/CI recovery path for the current storage layer, not a new
maintenance commitment or production security approval. P-001's third-party/release review
still applies; the platform's root license remains a separate decision.

Local and DigitalOcean use the same Compose build contract. No new service, public port or
credential is introduced. Hosted deployment and existing-data upgrades need their own
acceptance; fresh CI proof cannot certify either.

## Verification

Offline checks verify source/base pins, narrow build contexts and retained storage boundaries.
CI builds both targets and runs the live creator journey. The in-app setup bundle includes
this recipe/provenance so installed apps can perform the same build. Native/physical acceptance
and licensing/security sign-off remain in the owning proposals.
