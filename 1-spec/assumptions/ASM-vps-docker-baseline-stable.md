# ASM-vps-docker-baseline-stable: A Docker-capable VPS baseline is stable enough across providers without provider-specific patches

**Category**: Environment

**Status**: Unverified

**Risk if wrong**: Medium — if false in a way that requires provider-specific patches, the "any VPS" promise of [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) weakens to "any VPS in a known-good list," and Ben's disaster-recovery posture (rebuild on a new provider in <1 h) becomes contingent on that list. The remediation is bounded — the install script can grow provider-detection branches, the runbook can document an "approved providers" list, and provider-specific quirks can be captured as `DEC-vps-provider-quirk-*` — but every quirk added pays an ongoing maintenance cost.

## Statement

A "Docker-capable VPS at the reference hardware spec" — vanilla Ubuntu 22.04 / 24.04 or Debian 12, Docker Engine ≥ 24, Docker Compose v2, 4 vCPU, 8 GB RAM, ≥ 50 GB disk — is a stable enough baseline across realistic VPS providers (Hetzner, Contabo, Hetzner Cloud, Scaleway, Linode/Akamai, OVH, generic KVM hosts) that the install + smoke test produces functionally identical results on each, without provider-specific patches for:

- Networking (overlay-network behavior, IPv6 dual-stack defaults, DNS resolver quirks, MTU mismatches)
- Container storage backends (overlay2 vs. zfs vs. btrfs)
- Filesystem semantics affecting volume restore (case sensitivity, sparse-file handling, extended attributes)
- Kernel feature availability (cgroups v2, seccomp profiles, user-namespace remapping)

## Rationale

Docker + Compose is specifically designed to abstract these differences, and the four channels of variability above are well-understood enough that mainstream Linux VPS providers converge on compatible defaults. The MVP system uses standard Compose features (named networks, named volumes, environment variables, healthchecks) without exotic overlays, capabilities, or kernel-level integrations.

The risk concentrates in three places: (1) IPv6 / dual-stack defaults vary across providers and have caused Compose networking issues in adjacent projects (cf. the user's earlier note about Hetzner IPv6); (2) some discount providers ship custom kernels that occasionally lack a Docker-required feature; (3) volume-backup compatibility across filesystem types may vary if `tar` flags miss extended attributes or sparse-file handling.

## Verification Plan

- **During Code/Deploy phase, before claiming [REQ-PORT-vps-deploy](../requirements/REQ-PORT-vps-deploy.md) complete:** run the full install + smoke test on at least two unrelated VPS providers designated by the operator. Document any deltas. If a provider requires a workaround, capture it as a `DEC-vps-provider-quirk-<provider>` decision and either (a) generalize the workaround into `install_vps.sh` (preferred), or (b) document the provider as "tested with workaround X" in the install runbook, or (c) document the provider as unsupported.
- **Trigger for re-verification:** any new provider added to the operational pool; any base-image upgrade (Ubuntu LTS bump, new Compose major version); any reported install/smoke regression.

## Related Artifacts

- Goals: [GOAL-local-portable-deployment](../goals/GOAL-local-portable-deployment.md)
- Requirements: [REQ-PORT-vps-deploy](../requirements/REQ-PORT-vps-deploy.md), [REQ-REL-backup-restore-fidelity](../requirements/REQ-REL-backup-restore-fidelity.md), [REQ-MNT-env-driven-config](../requirements/REQ-MNT-env-driven-config.md)
- Constraints: [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md)
