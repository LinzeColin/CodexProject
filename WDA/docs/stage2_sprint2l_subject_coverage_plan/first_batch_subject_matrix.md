# First-Batch Subject Matrix

## Inclusion / Exclusion

Explicitly include up to five first-batch subject targets:

1. `马祥荣 / 雁`
2. `老婆`
3. `付款/发票/金额相关联系人`
4. `近期高频联系人`
5. `弱匹配/噪音样本`

Explicitly exclude:

- `李晶工作交接`: pollution/noise source, not a subject sample.

## Subject Matrix

| Subject target | Identity tokens | Lookup strategy | Fallback if exact contact not found | Max export size | Expected validation fields | Success criteria | Failure criteria |
|---|---|---|---|---:|---|---|---|
| `马祥荣 / 雁` | `马祥荣`, `雁`, possible alias overlap | Search sessions/contact display labels and recent sessions for both exact and alias tokens | Export the best single candidate with shape-only evidence; if two plausible candidates exist, export the smaller bounded sample from each only if total cap still holds | 100 messages | `conversation_id`, `sender_id`, `direction`, `timestamp_ms`, `message_type`, `text`, `source_record_ref` | At least one matching conversation exports and validates without conversion errors | No candidate found, ambiguous candidate cannot be bounded, or export requires full history |
| `老婆` | `老婆`, spouse label, owner-known alias if visible in session list | Search exact display label first, then pinned/frequent direct sessions | If exact label absent, use owner-approved high-confidence spouse alias only; otherwise mark not found | 100 messages | Same as above plus direct/private conversation classification | One bounded direct/private export validates | Candidate not found or only group/noise matches found |
| `付款/发票/金额相关联系人` | `付款`, `发票`, `金额`, `转账`, `收款`, `报销`, currency-like terms in session labels if available | Prefer session/contact name tokens; do not content-search full history unless the tool supports bounded metadata-safe search | Select up to one highest-confidence payment/invoice-related conversation; if none, mark no metadata match | 100 messages | Same as above plus message type distribution | One bounded relevant conversation validates, or no-match is documented cleanly | Requires content-wide search, full export, or broad account scan |
| `近期高频联系人` | recent/frequent session rank, unread/recent activity, non-folded session | Use recent sessions list and choose the highest-frequency non-excluded, non-duplicate candidate | If top candidate is excluded/noise, move to next eligible recent high-frequency candidate | 100 messages | Same as above plus source selection rank | One recent high-frequency conversation validates | Only excluded/noise/folded sessions are available |
| `弱匹配/噪音样本` | low-confidence alias, ambiguous label, likely irrelevant session | Select one deliberately weak or noisy candidate to test false-positive handling | If no weak candidate is available, use a clearly non-target recent session with minimal scope | 100 messages | Same as above plus classification label `noise_sample` in reports | Export validates and is marked as noise/control, not target evidence | Noise sample is accidentally treated as a target or contains excluded source |

## Cap

Sprint 2M must stop at the first of:

- 5 subject targets
- 100 messages per subject/conversation
- 500 total messages

