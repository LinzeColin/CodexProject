# Subject Identity Seed Requirements

## Purpose

Sprint 2M needs subject identity seeds before export so it can select bounded
conversations without broad search or full history export.

## Required Seed Fields

For each subject target, Sprint 2M should record:

- `subject_id`
- `subject_label`
- `identity_tokens`
- `positive_aliases`
- `negative_tokens`
- `selection_reason`
- `lookup_method`
- `fallback_rule`
- `max_messages`
- `noise_or_target`

## Initial Seeds

| subject_id | subject_label | identity_tokens | negative tokens | max_messages | noise_or_target |
|---|---|---|---|---:|---|
| `S2M-SUBJ-01` | `马祥荣 / 雁` | `马祥荣`; `雁` | `李晶工作交接` | 100 | target |
| `S2M-SUBJ-02` | `老婆` | `老婆`; owner-known spouse alias if visible | `李晶工作交接` | 100 | target |
| `S2M-SUBJ-03` | `付款/发票/金额相关联系人` | `付款`; `发票`; `金额`; `转账`; `收款`; `报销` | `李晶工作交接` | 100 | target |
| `S2M-SUBJ-04` | `近期高频联系人` | recent session rank; frequent direct/group contact | `李晶工作交接`; already selected subjects | 100 | target |
| `S2M-SUBJ-05` | `弱匹配/噪音样本` | weak alias; ambiguous candidate; non-target recent session | all target tokens; `李晶工作交接` | 100 | noise_control |

## Non-Goals

- Do not require full-contact export.
- Do not require all-history search.
- Do not content-search all messages unless a later sprint separately approves a
  bounded content-search method.

