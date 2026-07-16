# Qpet release checklist

## Final skill gate

- [x] The active skill test run has completed successfully.
- [x] The approved source snapshot has been synced with `scripts/sync_snapshot.py`.
- [x] Unit tests pass from `plugins/qpet/tests`.
- [x] `scripts/verify_marketplace.py` passes.
- [x] Both release ZIP files build and pass archive integrity checks.

## Product review

- [x] Brand name is consistently shown as **Qpet**.
- [x] Plugin identifier, folder name, and marketplace entry are all `qpet`.
- [x] Logo, dark logo, composer icon, and Skill icons use the approved 奶油卷 cat avatar.
- [x] Selfie consent and source-photo handling remain explicit.
- [x] Qpet does not claim to open the camera silently.
- [x] Qpet does not claim to add new native mouse interactions or a native usage HP overlay.
- [x] Exactly five positive and three negative review cases remain present.
- [x] No credentials, tokens, private keys, personal photos, or local test output are included.

## GitHub publication

- [x] Replace `OWNER` in the public installation examples with the real GitHub owner.
- [x] Create a public GitHub repository named `qpet`.
- [x] Review the repository license and publisher name.
- [x] Push the `main` branch.
- [x] Test installation from a clean Codex profile using the GitHub repository.
- [ ] Confirm the `main` branch GitHub check passes.
- [ ] Create tag `v1.0.2`.
- [ ] Attach the two ZIP files and `SHA256SUMS.txt` to the GitHub Release.
- [ ] Keep the OpenAI universal-directory submission separate from this community release.
