# Position & Stop-Loss Calculator

[Open the live calculator](https://raw.githack.com/loongw320-alt/portfolio/main/position-calc/index.html). The interface is in English by default; tap **中文** to switch, and your choice is remembered.

## Features and local use

Open `index.html` directly in your browser; no installation, build step, connection or server is required. The responsive bilingual (English / 中文) interface computes everything locally with no dependencies, uploads or order placement. Change inputs for automatic updates, or click the calculate button.

Enter capital, risk budget, entry price, stop price, leverage, direction and maintenance-margin rate. Use one consistent quote currency (USDT in the examples). Long stops must be below entry; short stops above entry. Enter `0.5` for a 0.5% maintenance-margin rate; the default is illustrative. Outputs are underlying-coin quantity, entry notional, initial margin, theoretical stop loss and an approximate liquidation price. Invalid inputs clear results and explain the error.

## Model and formulas

The model applies to a single isolated, stablecoin-margined linear position. It assumes initial margin equals entry notional divided by leverage, no extra collateral, and maintenance margin based on current notional at a fixed rate. It excludes tier deductions.

Let capital = B, risk budget = R, entry = E, stop = S, leverage = L and maintenance rate as a fraction = m.

- Quantity: Q = R / |E − S|
- Entry notional: N = Q × E
- Initial margin: M = N / L
- Theoretical stop loss: D = Q × |E − S| = R
- Long liquidation estimate: P = E × (1 − 1/L) / (1 − m)
- Short liquidation estimate: P = E × (1 + 1/L) / (1 + m)

Liquidation estimates solve equity = maintenance margin: M + Q(P − E) = QPm for longs, and M + Q(E − P) = QPm for shorts. A 1× long produces a model price of zero; this is not a guarantee against actual liquidation or fee risks. With fixed risk, entry and stop, leverage changes margin and liquidation estimates, but not quantity or theoretical stop loss.

Inputs require B, R, E, S > 0; L ≥ 1; 0 ≤ m < 1; and 1/L > m. Quantity is underlying coins, not exchange contract counts. Convert using contract multipliers, minimum quantities and step sizes, round down and recalculate before using elsewhere. Displayed numbers are rounded, internal calculations are not; tiny values use scientific notation.

## Output example and warnings

Capital 1,000 USDT, risk 20 USDT, entry 60,000, stop 59,000, 10× long and maintenance rate 0.5% produce:

| Output | Value |
| --- | ---: |
| Quantity | 0.02 coins |
| Entry notional | 1,200 USDT |
| Initial margin | 120 USDT |
| Theoretical stop loss | 20 USDT |
| Approximate liquidation price | 54,271.3568 USDT/coin |

Warnings appear when the stop is at or beyond the liquidation estimate (S ≤ P for longs, S ≥ P for shorts), margin exceeds capital, or risk exceeds capital. Inputs with 1/L ≤ m are rejected because modeled initial equity is already at or below maintenance margin.

## Limitations

Educational arithmetic only, not investment advice, a return promise or a trade instruction. Excludes trading and funding fees, slippage, gaps, liquidation fees, risk tiers, maintenance deductions, other positions and changing account equity. Not applicable to cross margin, portfolio margin or inverse coin-margined contracts. Exchanges generally liquidate using mark prices; stop triggers may use different prices and cannot guarantee execution or cap actual losses. Verify actual margin requirements and liquidation estimates with the exchange.

---

# 加密合约仓位 / 止损计算器

直接用浏览器打开 `index.html` 即可使用，无需安装、联网或构建。页面支持英文/中文切换（默认英文，点右上角“中文”切换），适配手机，所有计算在本地执行，无第三方依赖、数据上传或下单功能。

## 用法

1. 输入本金与本次愿意承担的风险金额，两者均以 USDT 为例；同一计算内必须使用一致的报价币种。
2. 输入入场价、止损价、杠杆和多空方向。做多止损价须低于入场价，做空须高于入场价。本工具测算新开仓的风险，不用于已有盈利仓位的移动止损。
3. 根据目标交易所与仓位档位输入维持保证金率。输入 `0.5` 表示 `0.5%`，默认值只是演示参数。
4. 参数修改后自动计算，也可点击计算按钮。查看数量、名义价值、保证金、止损亏损和爆仓价近似值，以及风险提示。

数量单位为标的币数量，不是交易所的合约张数。真实下单须按合约乘数、最小数量和步长换算并向下取整，再重新核算。页面显示会舍入，但内部使用未舍入值计算；极小数字用科学计数法显示。

## 模型与公式

适用于稳定币本位线性合约、单个逐仓仓位。假设全部初始保证金为名义价值除以杠杆，无追加保证金；维持保证金按当前价格下的仓位价值与固定维持保证金率计算，不含维持保证金速算扣除额。

记本金为 B，风险金额为 R，入场价为 E，止损价为 S，杠杆为 L，维持保证金率为 m（百分比输入值除以 100）。

- 仓位数量：Q = R / |E − S|
- 入场名义价值：N = Q × E
- 初始所需保证金：M = N / L
- 理论止损亏损：D = Q × |E − S| = R
- 做多爆仓价：P = E × (1 − 1/L) / (1 − m)
- 做空爆仓价：P = E × (1 + 1/L) / (1 + m)

爆仓公式来自“账户权益 = 维持保证金”：做多时 M + Q(P − E) = QPm，做空时 M + Q(E − P) = QPm。1 倍做多的模型爆仓价为 0，不代表真实交易免于强平或费用风险。

相同风险金额、入场价和止损价下，杠杆不改变数量与理论止损亏损，只改变所需保证金和爆仓价。要求 B、R、E、S > 0，L ≥ 1，0 ≤ m < 1，且 1/L > m；无效输入将清空结果并显示原因。

## 示例与提示规则

本金 1000、风险 20、入场 60000、止损 59000、10 倍做多、维持保证金率 0.5% 时：数量 0.02 币，名义价值 1200 USDT，保证金 120 USDT，理论止损亏损 20 USDT，爆仓价约 54271.3568 USDT / 币。

- 做多 S ≤ P、做空 S ≥ P：警告止损在爆仓价之外或与其重合，可能先强平。
- M > B：警告保证金超过本金。
- R > B：另行警告风险预算超过本金。
- 1/L ≤ m：拒绝计算，因为按本模型入场权益已经不高于维持保证金。

## 免责声明

本工具仅用于学习和数学估算，不构成投资建议、收益承诺或交易指令。未计入手续费、资金费、滑点、跳空、强平费用、风险限额档位、维持保证金扣除额、其他仓位和账户权益变化。不适用于全仓、组合保证金或币本位反向合约。交易所通常依据标记价格触发强平，止损可能采用不同触发价格；即使显示止损在爆仓价之前，也不能保证先成交或将实际损失限制在风险金额内。实际保证金和强平价格应以交易所规则与订单预览为准，使用者自行核对并承担风险。
