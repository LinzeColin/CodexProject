# Memory Atlas Next Action Model

- Contract ID: `next_action_model_v1_1_7_stage1_phase2`
- Task ID: `MA-V117-S1P02`
- Acceptance ID: `ACC-MA-V117-S1P02`
- Status: `phase_1_2_next_action_detail_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase2`

## Purpose

The Next Action model turns Memory Atlas state signals into a small ranked list
of explainable suggested actions. It must help the user decide what to do next,
why it matters, what evidence supports it, and what a safe proposal-only follow
up would be.

This phase implements suggested action visibility and detail only. It does not
implement tier asset detail, topic classification detail, a proposal editor,
agent apply, production build, app reinstall, deploy or GitHub main upload.

## Required Fields

Each action detail must expose:

| Field | Required | Source | Display |
|---|---|---|---|
| `action_id` | yes | deterministic action builder | card, drawer, Inspector handoff |
| `title` | yes | action model summary | card, drawer |
| `action_type` | yes | continue/review/consolidate/explore/defer | drawer |
| `reason` | yes | source signal explanation | card, drawer |
| `roi_score` | yes | ROI / leverage heuristic | card, drawer |
| `effort_cost` | yes | low/medium/high effort estimate | card, drawer |
| `urgency` | yes | high/medium/low urgency | card, drawer |
| `confidence` | yes | evidence strength and model certainty | drawer |
| `source` | yes | redacted derived source or runtime model | drawer |
| `status` | yes | proposed/review/blocked/done-safe | drawer |
| `evidence_count` | yes | redacted evidence or connected edge count | card, drawer |
| `evidence_refs` | yes | redacted node IDs, source labels or derived refs | drawer |
| `matched_reason` | yes | why this action was selected | drawer |
| `linked_topic_ids` | yes | theme or cluster IDs | drawer |
| `linked_asset_ids` | yes | memory node IDs | drawer |
| `next_step` | yes | concrete next user step | card, drawer |
| `recommended_time_window` | yes | now/today/this_week/later | drawer |
| `proposal_hint` | yes | proposal_recommended/proposal_not_needed | drawer |
| `rollback_hint` | yes | how to undo the proposed change safely | drawer |
| `proposal_only` | yes | must be true | card, drawer |

## Sort Model

The runtime function `nextActionSortScore` ranks candidate actions with:

```text
sort_score =
  roi_score * roi_weight
  + urgency_score * urgency_weight
  + confidence * confidence_weight
  - effort_penalty * effort_penalty_weight
```

Default v1.1.7 weights:

| Weight | Value |
|---|---:|
| `roi_weight` | 0.40 |
| `urgency_weight` | 0.25 |
| `confidence_weight` | 0.25 |
| `effort_penalty_weight` | 0.10 |

The list is capped at Top 5. If fewer than five candidate signals exist, the
model shows all available actions and must explain empty/fallback states rather
than invent mock actions.

## Runtime Mapping

| Runtime surface | Requirement |
|---|---|
| Home action cards | Show priority, ROI, effort, urgency, evidence count and next step. |
| `ActionDetailDrawer` | Show reason, ROI, effort, urgency, confidence, source, evidence refs, matched reason, linked topics/assets, proposal hint and rollback hint. |
| Inspector handoff | If the action has a linked node, selecting the action can synchronize the current focus before navigating. |
| Proposal safety | Actions may recommend proposal-only follow up but cannot write proposal JSON or active memory in this phase. |

## Safety Boundary

- `proposal_only` must be true for every generated action.
- No raw/private/cookie/session/secret/plaintext transcript data may be read or
  displayed.
- No direct writeback is allowed.
- No proposal write is allowed in Phase 1.2.
- No GitHub main upload is allowed before whole Stage 0-8 completion.

## Rollback

Revert the Stage 1 Phase 1.2 commit. This removes the model, drawer, validator,
package script and records without migrating data or changing active memory.
