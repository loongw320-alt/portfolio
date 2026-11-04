# Funding Rate Arbitrage Calculator / 资金费率套利计算器

Open `index.html` directly in a browser. No installation, server, network, fonts, CDN, or dependencies required. Keep `calc.js` beside it. English is the default; the top-right button switches to Chinese. All inputs and results stay local. Layout adapts to mobile screens.

直接在浏览器打开 `index.html`，保持 `calc.js` 与其同目录。无需安装、服务器、网络或外部依赖。默认英文，右上角切换中文，支持手机屏幕，所有计算均在本地完成。

## Model and formulas / 模型与公式

The strategy holds equal notionals of long spot and short perpetual. `L` is leverage on the perpetual leg, **not** leverage on total principal. All amounts share a quote currency. Rates entered in the UI are percentages; the formulas below use decimal rates (e.g. 0.01% → 0.0001).

策略为等额现货多头 + 永续空头。`L` 是**永续腿杠杆**，不是整体本金杠杆。金额均使用相同计价币种。界面费率单位为百分比，以下公式使用小数费率（如 0.01% → 0.0001）。

| Symbol / 符号 | Meaning / 含义 |
| --- | --- |
| P | Principal / 本金，P > 0 |
| L | Perpetual leverage / 永续杠杆，L ≥ 1 |
| f | Funding rate per settlement / 每次资金费率，可为负 |
| h | Settlement interval in hours / 结算间隔小时数，默认 8，h > 0 |
| D | Holding days / 持有天数，D ≥ 0 |
| sₒ, s꜀, pₒ, p꜀ | Spot and perpetual opening/closing fee rates / 现货与永续分别开平仓的手续费率，均 ≥ 0 |

- **Per-leg notional / 每腿名义仓位:** `N = P / (1 + 1/L) = P × L / (L + 1)`.
- **Allocation / 本金分配:** spot / 现货 `N`; perpetual margin / 永续保证金 `N/L`; total / 合计 `P`. Gross absolute exposure / 两腿绝对敞口合计 `2N`.
- **Settlements / 结算次数:** `K = floor(24D/h)`; first settlement at `h` hours, inclusive of the closing boundary. Floating-point noise at exact boundaries is normalized. / 首次结算在 h 小时后，平仓时点恰好结算则计入，修正浮点边界误差。
- **Funding / 资金费收入:** `F = N × f × K`. Positive funding pays the short; negative funding is an expense. / 正费率空头收款，负费率空头付款。
- **Round-trip fees / 两腿开平仓总手续费:** `C = N × (sₒ + s꜀ + pₒ + p꜀)`.
- **Net profit / 净收益:** `Π = F − C`.
- **Return on principal / 本金收益率:** `R = Π/P`.
- **APR / 线性年化:** `R × 365/D`, available only when `D > 0` / 仅 D > 0 时适用。
- **Hypothetical APY / 假设复投年化:** `(1 + R)^(365/D) − 1`. Available for `D > 0` and `R > −1`; unrepresentable results display N/A. / 仅 D > 0 且 R > −1 时适用；数值溢出显示不适用。
- **Break-even / 手续费回本天数:** when `f > 0`, `ceil(C/(Nf)) × h/24`; zero fees yield 0; otherwise with nonpositive funding it is never reached. The estimate may exceed the selected holding period. / 正费率时按完整结算次数向上取整；无手续费时为 0；有手续费且费率非正时无法回本，回本时间可能超过输入持有期。

Default example / 默认示例: `P = 10,000`, `L = 3`, `f = 0.01%`, `h = 8`, `D = 30`, spot fees / 现货开平各 `0.1%`, perpetual fees / 永续开平各 `0.05%`. Each leg / 每腿 `7,500`; margin / 保证金 `2,500`; settlements / 结算 `90`; funding / 资金费 `67.50`; fees / 手续费 `22.50`; net / 净收益 `45.00`; ROI / 收益率 `0.45%`; APR `5.475%`; break-even / 回本 `10 days / 天`.

## Assumptions and risks / 假设与风险

Prices, notional and funding rates remain constant. The perpetual is linear and quote-margined with matching spot exposure. Entry occurs immediately after a settlement. Fees use the same fixed notional at entry and exit, even for a zero-day round trip. All principal is allocated to spot and margin; **no fee or liquidation buffer is reserved**. Fees are deducted from the modeled return; actual trading needs sufficient available funds for fees and margin requirements. No borrowing costs, spread, slippage, collateral yield, taxes, price/basis P&L or transfers are modeled.

假设价格、名义仓位和资金费率恒定，采用计价币保证金的线性永续，现货与合约敞口匹配。假设刚结算后入场；开平仓按相同名义仓位收取手续费，持有 0 天也计完整往返费用。本金全部用于现货和保证金，**不预留手续费或清算缓冲**；手续费从模型收益扣除，实盘需要额外可用资金满足手续费与保证金要求。不计借贷成本、买卖价差、滑点、抵押品利息、税费、价格或基差损益与划转。

APY assumes repeating identical holding cycles, paying round-trip fees each cycle, and reinvesting all profits with unchanged conditions. It is a mathematical extrapolation, not a forecast. Negative or changing funding, liquidation, basis divergence, liquidity, exchange/counterparty failures and stablecoin depegging can create losses. Delta neutrality does not prevent liquidation: spot profits may not be available to support isolated perpetual margin. Educational scenario calculator, not investment advice or a guarantee of profit.

APY 假设不断重复相同持仓周期、每周期支付完整开平手续费、收益全部复投且条件不变，只是数学外推而非预测。费率转负或变化、爆仓、基差偏离、流动性不足、交易所或交易对手违约、稳定币脱锚均可能导致亏损。Delta 中性不能避免爆仓，现货盈利未必可及时补充逐仓永续保证金。仅供情景估算与学习，不构成投资建议或收益保证。

## Tests and API / 测试与接口

Run / 运行: `node test.js` (Node.js built-in `assert`, no packages / 内置 assert，无依赖).

```js
const { calculate } = require('./calc.js');
const result = calculate({ principal: 10000, leverage: 3, fundingRate: 0.01 });
console.log(result.netProfit); // 45; omitted fields use UI defaults / 省略字段使用界面默认值
```

The pure function accepts numeric inputs only, does not mutate them, and throws `RangeError` on invalid or overflowing inputs. Returned ROI/APR/APY use decimal fractions. `null` means an undefined annualization or unreachable break-even. APY also returns `null` on overflow. / 纯函数只接受数值输入，不修改输入；无效或超范围输入抛出 `RangeError`。返回的收益率、APR、APY 为小数；`null` 表示年化不适用、无法回本，或 APY 溢出。

Files / 文件: `index.html` (UI / 界面), `calc.js` (pure calculation / 纯计算), `test.js` (tests / 测试), `README.md` (documentation / 说明).
