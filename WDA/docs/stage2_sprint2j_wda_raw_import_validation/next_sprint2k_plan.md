# Next Sprint 2K Plan

## Recommended Next Sprint

Sprint 2K: bounded repeatability and coverage validation.

## Goal

Prove that the automated acquisition route can repeatedly produce
WDA-compatible message-level artifacts beyond a one-message sample.

## Proposed Scope

- Stay on the old computer for acquisition if additional live WeChat reads are
  required.
- Keep the new computer as WDA Control Plane and validation host.
- Use only approved bounded exports.
- Increase sample scope cautiously, for example:
  - more messages from the same conversation
  - one additional conversation
  - selected message types without media enrichment first
- Transfer only the minimum artifact needed for validation.
- Continue keeping raw outputs under WDA_MetaData only.

## Stop Conditions

- Tool requires full export before bounded samples.
- Tool requires transferring key material.
- Tool writes outside approved WDA_MetaData paths.
- Media enrichment blocks text-only repeatability.
- Any command attempts upload, message sending, or UI automation.

## Gate

Raw Gate can only move beyond `Sample Message-Level Proven` after repeatable,
bounded, validated samples prove broader coverage.

