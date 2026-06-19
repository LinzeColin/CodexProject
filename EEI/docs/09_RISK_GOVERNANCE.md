# 09 - Risk and Governance

## 1. Product risks

### Commercial empire overclaim

Risk: 用户把综合视图误解为法律控制。  
Control: relationship layer labels、legal/economic/strategic distinction、human summary disclaimers、evidence.

### Graph recursion explosion

Risk: 连续展开造成性能、成本和可读性崩溃。  
Control: bounded query、lazy expansion、grouping、new workspace、truncation explanation.

### Visual centrality bias

Risk: 图中居中/大节点被认为更有权力。  
Control: node size selectable、score explanation、fixed layout option、table alternative.

### Hidden-money illusion

Risk: 公共数据被包装成“真实隐藏资金”。  
Control: amount_kind、report/filed/observed、unknown/coverage、no real-time claim.

## 2. Supply-chain risks

- Tier-2/Tier-3 不透明；
- supplier/customer identity resolution errors；
- product/facility/legal entity混淆；
- contract amount vs actual volume；
- geographic and policy data stale；
- company publicity bias。

Controls: evidence thresholds、derived labels、coverage、stage ontology、manual review、biweekly calibration.

## 3. Model risks

### False precision

Control: raw/quality/adjusted/coverage separate；missing inputs visible；no decimals beyond useful precision.

### User confirmation bias

Control: frozen default profile、counter-evidence、preview side effects、operation logs、calibration report.

### Weight overfitting

Control: no short-term price optimization；14-day review；proposal not auto-activate；rollback.

### Model drift

Control: score distribution、Top-N stability、source coverage and gold precision in calibration.

## 4. Data and compliance risks

- source terms/licensing；
- robots/access controls；
- PII leakage in logs；
- stale private-company facts；
- 13F or government amount semantics；
- cross-source conflict。

Controls: source registry、allowlist、no bypass、minimal logs、freshness、specific amount types、conflict records.

## 5. Engineering risks

- irreversible migration；
- partial publish；
- unsafe network/permissions；
- dependency vulnerability；
- background scheduler nondeterminism；
- URL state incompatible with schema versions。

Controls: migration round-trip、transactional batch、sandbox/network-off、lockfiles/audit、fixture clock、state versioning.

## 6. Stop conditions

- 需要违反访问控制/许可；
- 必须引入不可回滚 migration；
- 核心事实无法验证却被要求标成 reported；
- 评分被要求输出收益概率；
- calibration 被要求未经审查自动改 active profile；
- 高危安全问题未处置；
- P0 acceptance 定义需实质改变。

## 7. Governance artifacts

- `docs/11_DECISION_LOG.md`
- `data/risk_register.csv`
- `operation_logs`
- `calibration_runs`
- release report and benchmark environment
- source terms notes and last verified
