# Alipay / Off-Platform Fund Execution Window Evidence

Generated: 2026-06-13 AEST

## Executive Conclusion

For standard mainland open-end fund transactions through fund sales platforms, the working rule is:

- A trading-day order submitted before 15:00 Beijing time is generally treated as T-day.
- It is generally priced by the fund NAV for that T-day, not by an intraday exchange price.
- Domestic ordinary open-end fund shares are commonly confirmed on T+1 working day and queryable later, often T+2.
- Orders after 15:00, weekends, and holidays normally roll to the next fund trading/open day.
- QDII, Hong Kong/global, special products, suspended products, conversion, fast redemption, or fund-specific announcements can override the general rule.

Operational impact for Serenity Daily Analysis:

- Treat the 14:30 Beijing run as the final pre-cutoff execution-window review.
- Treat 15:30, 16:30, and 17:30 Beijing runs as post-cutoff discipline/review windows unless the fund page states otherwise.
- Any rebalance instruction must still check the target fund's Alipay page or fund-company rule page for current subscription/redemption status, fee schedule, limit, confirmation lag, and special calendar.
- This evidence supports the rule model only; it does not unlock production execution without real holdings and fund-rule intake.

## Source Evidence

| Priority | Source | Evidence Type | URL | Finding |
|---:|---|---|---|---|
| 2 | Alipay / Tianhong agreement | Alipay-hosted fund agreement | https://render.alipay.com/p/yuyan/180020010001201259/bank/THSGXY.htm?page=THSGXY | If a deduction day is not an open day, the subscription is postponed to the next application day; subscribed shares are confirmed into the investor fund account on T+1. |
| 3 | Tiantian Fund Help Center | Licensed fund sales platform help | https://help.1234567.com.cn/question_243.html | T-day is bounded by the stock-market close; transactions before 15:00 use the same day's NAV, while after 15:00 uses the next trading day's NAV; T+1 confirmation is described. |
| 3 | Tiantian Fund Help Center | Licensed fund sales platform help | https://help.1234567.com.cn/question_247.html | General fund redemption is confirmed on T+1 working day; result query is generally T+2; redemption arrival varies by fund type. |
| 3 | Bank of China investor education | Bank fund-sales education | https://www.boc.cn/custserv/cs7/cs73/200808/t20080819_1306.html | Same-day subscription and redemption applications can be revoked before 15:00; confirmation/query timing and fund contract/prospectus review are emphasized. |
| 2 | E Fund official announcement PDF | Fund-company official announcement | https://cdn.efunds.com.cn/owch/data/bulletin/20260611/%E6%98%93%E6%96%B9%E8%BE%BE%E7%A0%94%E7%A9%B6%E6%99%BA%E9%80%89%E8%82%A1%E7%A5%A8%E5%9E%8B%E8%AF%81%E5%88%B8%E6%8A%95%E8%B5%84%E5%9F%BA%E9%87%91%E5%BC%80%E6%94%BE%E6%97%A5%E5%B8%B8%E7%94%B3%E8%B4%AD%E3%80%81%E8%B5%8E%E5%9B%9E%E3%80%81%E8%BD%AC%E6%8D%A2%E5%92%8C%E5%AE%9A%E6%9C%9F%E5%AE%9A%E9%A2%9D%E6%8A%95%E8%B5%84%E4%B8%9A%E5%8A%A1%E7%9A%84%E5%85%AC%E5%91%8A.pdf | A current fund-company announcement states that T-day application NAV is used for subscription-share calculation and shares are usually confirmed on T+1 working day; it also says the fund manager treats valid applications received before trading-time end as T-day. |

## Rule For Automation

| Run Slot | Beijing Time | Default Trading Interpretation |
|---|---:|---|
| R1 | 08:30 | Pre-market evidence refresh only |
| R2 | 09:30 | Market-open evidence refresh |
| R3 | 10:30 | Morning intraday comparison |
| R4 | 11:30 | Midday review |
| R5 | 12:30 | Midday evidence refresh |
| R6 | 13:30 | Pre-cutoff preparation |
| R7 | 14:30 | Last practical pre-cutoff evidence window |
| R8 | 15:30 | Post-cutoff review, next-trading-day action planning |
| R9 | 16:30 | Post-close report and archive |
| R10 | 17:30 | Final daily archive and next-run preparation |

## Automation Constraint

The automation may generate:

- action labels;
- target weights;
- manual operation checklist;
- alert/warn/info emails or local notifications.

The automation must not:

- submit fund subscription/redemption/conversion orders;
- represent QDII/special-fund confirmation timing as T+1 without fund-page proof;
- treat general 15:00/T+1 evidence as enough to unlock production without current Alipay holdings and fund-specific rule evidence.
