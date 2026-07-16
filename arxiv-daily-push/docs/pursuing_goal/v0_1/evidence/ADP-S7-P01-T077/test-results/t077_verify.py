#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T077 acceptance: freeze the six-theme visual + key-motion baseline.

Acceptance (TASK_INDEX row 77): Owner 确认基线；reduced-motion 单独记录.
  (Owner confirms the baseline; reduced-motion is recorded separately.)
Deliverables: 6 themes x routes x 5 viewports screenshots, interaction recordings, asset hashes.
Objective: make the recently-restored themes + ambience layer an UN-DELETABLE contract.

Deterministic. Re-derives from the TOOL (visual_baseline) + the real worker source; re-computes the
asset hashes independently. This verifier checks the machine-verifiable backbone (the contract + hashes +
matrix + reduced-motion-separate + schema). The final "Owner 确认基线" is a HUMAN sign-off the implementer
does NOT self-sign -- the package is produced READY for Owner confirmation.

Load-bearing controls (the un-deletable contract must be enforced):
  * deleting a theme, mutating a theme token, changing an fx/hero mapping, or changing a hero video all
    change the asset hash and are flagged as a regression;
  * removing the reduced-motion rule changes its SEPARATE hash and is flagged.
"""
import importlib.util
import pathlib
import re
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB

fails = []
src = VB.WORKER.read_text(encoding="utf-8")
baseline = VB.build_baseline()
hashes = baseline["asset_hashes"]

# ================================================ deliverable: 6 themes x routes x 5 viewports
if len(baseline["themes"]) != 6 or set(baseline["themes"]) != set(VB.THEMES):
    fails.append(f"expected exactly the 6 themes, got {baseline['themes']}")
if len(baseline["viewports"]) != 5:
    fails.append(f"expected 5 viewports, got {len(baseline['viewports'])}")
if len(baseline["routes"]) < 6:
    fails.append(f"expected >= 6 routes, got {baseline['routes']}")
expected_cells = len(baseline["themes"]) * len(baseline["routes"]) * len(baseline["viewports"])
if baseline["matrix_cells"] != expected_cells or len(baseline["cells"]) != expected_cells:
    fails.append(f"matrix should be {expected_cells} cells, got {baseline['matrix_cells']}")
for t in VB.THEMES:                                   # every theme's rules/nav/fx/hero present in the contract
    c = VB.extract_contract()["themes"][t]
    if not (c["rules"] and c["nav"] and c["fx"] is not None and c["hero"] is not None):
        fails.append(f"theme {t} missing part of its contract (rules/nav/fx/hero)")
print(f"matrix: {len(baseline['themes'])} themes x {len(baseline['routes'])} routes x "
      f"{len(baseline['viewports'])} viewports = {baseline['matrix_cells']} cells")

# ================================================ deliverable: asset hashes (deterministic + distinct)
if VB.build_baseline()["asset_hashes"] != hashes:
    fails.append("asset hashes are not reproducible")
if len(set(hashes["per_theme"].values())) != 6:
    fails.append("the six theme fingerprints are not all distinct")
if "master_visual" not in hashes:
    fails.append("no master visual hash (the completeness anchor)")
# COVERAGE: the contract must capture MORE than the 6 colour-token blocks -- every theme's component
# rules and the motion themes' ambience CSS -- or it is an incomplete (false-safety) contract.
cov = baseline["coverage"]
if sum(cov["per_theme_rule_counts"].values()) <= 6:
    fails.append(f"contract too shallow -- only token blocks captured: {cov['per_theme_rule_counts']}")
for t in ("minimal", "techno", "cosmos"):     # the ambience (fx) themes must carry fx-layer motion CSS
    if cov["fx_rule_counts"][t] == 0:
        fails.append(f"ambience theme {t} has no fx-layer motion CSS captured (incomplete contract)")

# ---- UN-DELETABLE CONTRACT controls: each mutation must be detected as a regression ----
def regressed_elements(mutated_src):
    return {c["element"] for c in VB.detect_regression(hashes, mutated_src)["changes"]}

# (a) delete a theme entirely -- remove all of its `[data-theme="forest"]...` rules
del_src = re.sub(r'\[data-theme="forest"\][^{]*\{[^}]*\}', "", src)
if "theme:forest" not in regressed_elements(del_src):
    fails.append("control broken: deleting a theme's rules was not flagged")
# (b) mutate a theme colour token (change cosmos --ac accent)
if "theme:cosmos" not in regressed_elements(src.replace("--ac:#89AACC", "--ac:#000000", 1)):
    fails.append("control broken: mutating a theme token was not flagged")
# (c) change an fx (ambience) mapping: techno -> none would kill the ambience layer for techno
if "theme:techno" not in regressed_elements(src.replace("techno: 'techno'", "techno: 'none'", 1)):
    fails.append("control broken: changing an fx mapping was not flagged")
# (d) change a hero video (forest -> a different asset)
if "theme:forest" not in regressed_elements(src.replace("/media/aethera.mp4", "/media/gone.mp4", 1)):
    fails.append("control broken: changing a hero video was not flagged")
# (e) COMPLETENESS -- mutate the cosmos ambience-motion CSS (the galaxy layer): must be flagged
if "master_visual" not in regressed_elements(src.replace(".fx-cosmos .stars{", ".fx-cosmos .stars{opacity:0;", 1)):
    fails.append("control broken: an ambience-motion CSS change escaped the contract (incomplete)")
# (f) COMPLETENESS -- mutate a per-theme component rule (not the token block): must be flagged
if "theme:forest" not in regressed_elements(src.replace('[data-theme="forest"] .hero .cta{',
                                                         '[data-theme="forest"] .hero .cta{color:red;', 1)):
    fails.append("control broken: a per-theme component-rule change escaped the contract (incomplete)")
# (g) COMPLETENESS -- mutate the HERO_CSS constant: must be flagged
hero_head = VB._tmpl(src, "HERO_CSS")[:40]
if "hero_css" not in regressed_elements(src.replace(hero_head, "/*x*/" + hero_head, 1)):
    fails.append("control broken: a HERO_CSS change escaped the contract (incomplete)")
# (h) COMPLETENESS -- mutate a @keyframes rule (advanced motion): must be flagged
if "keyframes" not in regressed_elements(src.replace("@keyframes frise", "@keyframes ZZ_frise", 1)):
    fails.append("control broken: a keyframe (motion) change escaped the contract (incomplete)")
# (i) COMPLETENESS -- delete the hero <video> element (heroSection local const, not a top-level literal):
#     must be flagged via hero_markup + the video themes (the key motion the schema names)
if "hero_markup" not in regressed_elements(src.replace(
        '<video id="heroVideo" muted loop playsinline preload="auto" aria-hidden="true"></video>', "", 1)):
    fails.append("control broken: deleting the hero <video> escaped the contract (incomplete)")
# (j) COMPLETENESS -- rename the cosmos gauge arc (kills the count-up motion): must flag cosmos
if "theme:cosmos" not in regressed_elements(src.replace('id="gaugeArc"', 'id="gaugeGONE"', 1)):
    fails.append("control broken: renaming the cosmos gauge arc escaped the contract (incomplete)")
# (k) COMPLETENESS -- gut the blurChars() DOM producer (kills the techno blur-text-in key motion): must
#     flag techno. blurChars is a top-level function, not a template literal -- it must be hashed too.
gut_blur = src.replace(
    'return [...String(text)].map(c => c === \' \' ? \' \' : `<span class="bw">${esc(c)}</span>`).join(\'\');',
    'return esc(text);', 1)
if "theme:techno" not in regressed_elements(gut_blur):
    fails.append("control broken: gutting blurChars (techno blur-text-in) escaped the contract (incomplete)")
# (l) COMPLETENESS -- recolour the sparkSVG() DOM producer (cosmos dashboard sparkline): must flag cosmos
if "theme:cosmos" not in regressed_elements(src.replace('stroke="var(--ac)" stroke-width="1.5"',
                                                        'stroke="#ff0000" stroke-width="1.5"', 1)):
    fails.append("control broken: recolouring sparkSVG (cosmos sparkline) escaped the contract (incomplete)")
# (m) WIRING -- the PAGE shell injects the theme/motion identity into every page. Removing the ${FX_LAYERS}
#     injection un-wires the whole ambience/motion layer sitewide -- must flag page_shell (a frozen
#     ingredient PAGE stops injecting is inert).
if "page_shell" not in regressed_elements(src.replace("\n${FX_LAYERS}\n", "\n\n", 1)):
    fails.append("control broken: removing the PAGE ${FX_LAYERS} injection escaped the contract (un-wired)")
# (n) WIRING -- removing the <script>${THEME_JS}</script> injection kills every named key motion sitewide
if "page_shell" not in regressed_elements(src.replace("<script>${THEME_JS}</script>", "", 1)):
    fails.append("control broken: removing the PAGE ${THEME_JS} injection escaped the contract (un-wired)")
# (o) ENUMERATION -- THEME_OPTIONS lists which six themes the switcher offers. Removing a theme deletes it
#     from the product (its CSS/mappings survive as dead code) -- must flag theme_options + that theme.
rm_theme = src.replace("['cosmos', '宇宙星河'], ", "", 1)
assert rm_theme != src, "THEME_OPTIONS cosmos-entry anchor not found"
if not {"theme_options", "theme:cosmos"} <= regressed_elements(rm_theme):
    fails.append("control broken: deleting a theme from THEME_OPTIONS escaped the contract")
# (p) ENUMERATION -- corrupting a theme's value key (maps <option> to a bogus id -> applyTheme falls back
#     to warm, the theme unreachable) must flag.
if "theme_options" not in regressed_elements(src.replace("['cosmos', '宇宙星河']", "['cosmosX', '宇宙星河']", 1)):
    fails.append("control broken: corrupting a THEME_OPTIONS key escaped the contract")
# CROSS-CHECK: the tool's hardcoded six themes must equal the worker's offered set (THEME_OPTIONS) and the
# nav mapping -- and this consistency check must itself catch a theme removed from THEME_OPTIONS.
if not baseline["theme_set_consistency"]["consistent"]:
    fails.append(f"theme set inconsistent: {baseline['theme_set_consistency']}")
if VB.theme_set_consistency(VB.extract_contract(rm_theme))["consistent"]:
    fails.append("control broken: the theme-set consistency check must fail when a theme is removed")
# (q) RENDER-WIRING -- heroSection()'s `return video + dash` decides which hero DOM is assembled from the
#     (hashed) fragments. Changing it to `return video` drops the cosmos dashboard hero; `return ''` drops
#     all hero. heroSection's body must be hashed -> both must flag hero_section_fn + the hero themes.
if not {"hero_section_fn", "theme:cosmos"} <= regressed_elements(src.replace("return video + dash;", "return video;", 1)):
    fails.append("control broken: heroSection return-wiring `return video` escaped the contract")
if "hero_section_fn" not in regressed_elements(src.replace("return video + dash;", "return '';", 1)):
    fails.append("control broken: heroSection return-wiring `return ''` escaped the contract")
# (r) ASSET BYTES -- the hero videos are the hero motion; the contract must hash their BYTES, not just the
#     HERO_VIDEO paths (a byte-swap at the same path would otherwise be invisible). Independently sha256
#     the three assets: they must be distinct (a swap is detectable) and equal what the tool hashed; a
#     bogus path returns a MISSING marker (discrimination).
_vids = {"minimal": "velorah.mp4", "techno": "voyage.mp4", "forest": "aethera.mp4"}
_shas = {t: "sha256:" + __import__("hashlib").sha256((VB.ASSETS_MEDIA / f).read_bytes()).hexdigest()
         for t, f in _vids.items()}
if len(set(_shas.values())) != 3:
    fails.append("hero video assets are not distinct (a byte-swap would be undetectable)")
_va = VB.extract_contract()["hero_video_assets"]
for t in _vids:
    if _va.get(t) != _shas[t]:
        fails.append(f"tool did not hash the real bytes of {t}'s hero video")
if not VB._asset_sha("/media/__nonexistent__.mp4").startswith("<MISSING"):
    fails.append("control broken: a missing asset must be flagged, not silently hashed")
print(f"render-wiring + asset bytes: heroSection return hashed; 3 hero videos byte-hashed distinctly "
      f"({', '.join(t + '=' + _shas[t][7:15] for t in _vids)})")
# (s) FINAL WIRING LINK -- todayPage passes the hero into PAGE via `{ hero }`. Dropping it severs the
#     chain (no hero on the today page, a named key motion). Captured structurally (the heroSection call
#     line + the `{ hero }` pass count), so a todayPage CONTENT edit does not falsely trip it.
if "hero_wiring" not in regressed_elements(src.replace("return PAGE('/', body, { hero });", "return PAGE('/', body);", 1)):
    fails.append("control broken: dropping the todayPage `{ hero }` pass escaped the contract")
if VB.detect_regression(hashes, src.replace("为什么今天选它", "为什么今天选它 ", 1))["regressed"]:
    fails.append("control broken: a benign todayPage content edit must NOT trip the hero-wiring guard")
print("hero wiring: todayPage `{ hero }` pass hashed structurally (content-edit does not trip it)")
# non-regression: an unrelated NON-visual edit (server routing) must NOT flag anything
benign = src.replace("if (p === '/api/run')", "if (p === '/api/run' )", 1)
if VB.detect_regression(hashes, benign)["regressed"]:
    fails.append("control broken: a benign non-visual edit was mis-flagged as a regression")
print("un-deletable contract: delete-theme / token / fx-map / video / ambience-CSS / component-rule / "
      "HERO_CSS / keyframe / hero-<video> / cosmos-gauge / gut-blurChars / recolour-sparkSVG / "
      "PAGE-unwire-FX_LAYERS / PAGE-unwire-THEME_JS / THEME_OPTIONS-remove / THEME_OPTIONS-corrupt / "
      "heroSection-return-wiring / hero-video-bytes / todayPage-hero-pass all flagged (+ theme-set "
      "consistency cross-check); benign non-visual/content edit not flagged")

# ================================================ acceptance: reduced-motion 单独记录 (separate)
if not baseline["reduced_motion_separate"]:
    fails.append("reduced-motion is not recorded separately")
if "reduced_motion" not in hashes or hashes["reduced_motion"] == hashes["contract_root"]:
    fails.append("reduced-motion has no separate hash")
if "reduced_motion_variant" not in baseline["interaction_recording_schema"]:
    fails.append("the recording schema has no separate reduced-motion variant")
# negative control: removing the reduced-motion rule changes its SEPARATE hash
no_rm = src.replace("prefers-reduced-motion:reduce", "prefers-reduced-motion:xxxxxx", 1)
if "reduced_motion" not in regressed_elements(no_rm):
    fails.append("control broken: removing the reduced-motion rule was not flagged")
print("reduced-motion: recorded separately (own hash + recording variant); removal is flagged")

# ================================================ deliverable: screenshot + recording schema
ss = baseline["screenshot_schema"]
if not (ss["per_cell"] and ss["count"] == expected_cells):
    fails.append("screenshot schema does not cover every matrix cell")
rec = baseline["interaction_recording_schema"]
if not (rec["motion_themes"] and rec["recordings"]):
    fails.append("interaction-recording schema is empty")
# the 4 motion themes (fx != none or a hero video) must be exactly those recorded
motion_expected = [t for t in VB.THEMES if VB.extract_contract()["themes"][t]["fx"] != "none"
                   or VB.extract_contract()["themes"][t]["video"]]
if set(rec["motion_themes"]) != set(motion_expected):
    fails.append(f"motion themes {rec['motion_themes']} != expected {motion_expected}")
print(f"schema: {ss['count']} screenshots + recordings for motion themes {rec['motion_themes']}")

# ================================================ Owner gate not self-signed
if not baseline.get("owner_confirmation_required"):
    fails.append("baseline must require Owner confirmation (implementer does not self-sign the S7 gate)")

print("\nACCEPTANCE (machine-verifiable backbone) = " + ("PASS" if not fails else "FAIL"))
print("NOTE: final 'Owner 确认基线' is a human sign-off; this package is READY for Owner confirmation, "
      "not self-signed.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
