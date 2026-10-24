---
description: "Attack coverage gate — injection-point × vuln-class"
---

# /attack-coverage — Attack Coverage Gate

Read-only. Kiểm tra sổ coverage **attack-phase** (injection-point × vuln-class) cho target hiện tại. Đây là fix cho "lười khi test nhiều URL": chống agent test mẫu vài URL rồi báo "clean".

> Triết lý: đây là **coverage MEMORY, không phải recipe**. Bạn săn tự do; sổ chỉ ghi lại đã sờ tới đâu + bằng chứng, để KHÔNG thể tuyên bố "clean" trên point chưa hề soi. Floor, không phải ceiling. Chi tiết: `knowledge/patterns/attack-coverage-reasoning.md`.

---

## Execution

1. **Gate:** `python tools/attack_coverage.py check --target $ACTIVE_TARGET` (exit 1 = incomplete)
2. **Status:** `python tools/attack_coverage.py status --target $ACTIVE_TARGET`
3. **Next-work (chống satisfice):** `python tools/attack_critic.py --target $ACTIVE_TARGET`
   - `pending_always` / `pending_surface_required` = việc phải làm tiếp (always_test trước)
   - `no_finding_challenge` = high-value class báo clean → **confirm đã thử bypass-variants** (sqli: array-split/encoding/second-order/time-blind; …) chưa. *"Clean sau payload ngây thơ"* = đúng lỗi FIS survey.php.
   - `open_lane` = chain / second-order / business-logic / vendor / novel mà point này mời gọi
   - `outliers_incomplete` = point lạ (legacy/admin/gated/*-test) phải chạy **full mọi class**

## Nếu chưa có ledger

```bash
# từ output /find-params (mỗi dòng: endpoint<TAB>location<TAB>param)
python tools/attack_coverage.py init --target $ACTIVE_TARGET --points <points.txt>
# classify từng point bằng REASONING (không phải tra bảng cứng)
python tools/attack_coverage.py classify --target $ACTIVE_TARGET --point "URL | query | p" --surface-type string-param --rationale "..."
```

## Đóng 1 ô (mark) — bắt buộc EVIDENCE

```bash
# tested PHẢI kèm --evidence (payload + oracle); na PHẢI kèm --verify; finding kèm --ref
python tools/attack_coverage.py mark --target $ACTIVE_TARGET --point "URL | query | p" \
    --vclass sqli --status tested --evidence "' / array-split / time-based; WAF403 naive, array-split→backend no oracle = PARTIAL"
```
Bare tick (`tested` không evidence) bị **REJECT**. `na` trên always_test bị **REJECT**.

## Verdict

- `check` exit 0 + critic 0 pending → **ATTACK COVERAGE COMPLETE**
- Còn `pending` / `na-without-verify` / `tested-without-evidence` → **INCOMPLETE**, list cụ thể, force tiếp tục (override: `done --force`)
- Tự động enforce ở **report gate** `attack_coverage_complete` (block `/report` tới khi pass; skip nếu chưa có ledger)

## 2 modes (bạn chọn bằng cách giao việc — fan-out KHÔNG tự bật)

- 🔬 **deep-dive** (1 function, user+agent): ledger = scratchpad hiện ra, user override được (`skip --reason`), **KHÔNG** fan-out
- 🌊 **sweep** (nhiều URL, opt-in): ledger = hard gate + fan-out `.claude/workflows/multi_url_attack.js` (1 deep-attack subagent/point, full attention như single-URL)

Read-only — không modify file. Gọi bất kỳ lúc nào trong hunt loop; tự gọi khi hunter declare "done".
