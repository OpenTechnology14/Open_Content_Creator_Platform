# Kubernetes decision record

**Status:** deferred indefinitely. Revisit only when **all four** of the
following are true.

1. Docker Compose can no longer express our topology (e.g., we need true
   multi-host scheduling, not just multi-host networking through Tailscale).
2. We are routinely running ≥3 GPU burst workers and the manual SSH-and-pull
   pattern has caused at least one production incident.
3. We have a person whose explicit job includes operating the cluster, or
   we are paying for a managed cluster (DOKS, EKS, GKE).
4. The team has stopped iterating on the application layer for at least two
   weeks. (K8s is a tax — don't pay it while the product is still moving fast.)

## Why we are not on K8s today

- Compose is enough for a single host + a couple of remote workers.
- Tailscale gives us flat networking across local + cloud without an
  ingress controller.
- The realtime layer (OBS, DeepFaceLive, ComfyUI realtime) is intentionally
  local-first and would not move into a cluster anyway.
- The cost of running a control plane outweighs the benefit until we have
  ≥10 nodes or strict multi-tenant isolation needs.

## When we do move

Probable order:

1. Stand up DOKS with two app nodes + one GPU node.
2. Port FastAPI, NodeCG, AI agents, and observability first (stateless or
   easy to lift).
3. Move Postgres only after DO Managed PG → in-cluster has been justified.
4. GPU workers join as a separate nodepool with `node-selector` constraints.

See `docs/architecture/future.md` for the parking lot of related items.
