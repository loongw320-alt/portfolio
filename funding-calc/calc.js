(function (root) {
  'use strict';
  /** Rates are percentages; monetary outputs use the input principal's currency. */
  function calculate(input) {
    const defaults = { principal: 10000, leverage: 3, fundingRate: 0.01,
      intervalHours: 8, days: 30, spotOpen: 0.1, spotClose: 0.1,
      perpOpen: 0.05, perpClose: 0.05 };
    const p = { ...defaults, ...input };
    for (const key of Object.keys(defaults)) {
      if (typeof p[key] !== 'number' || !Number.isFinite(p[key]))
        throw new RangeError(`${key} must be a finite number`);
    }
    if (p.principal <= 0 || p.leverage < 1 || p.intervalHours <= 0 || p.days < 0 ||
        ['spotOpen', 'spotClose', 'perpOpen', 'perpClose'].some(k => p[k] < 0))
      throw new RangeError('Invalid input range');
    const notional = p.principal / (1 + 1 / p.leverage);
    const spotCapital = notional;
    const margin = p.principal - notional;
    // Snap only floating-point noise at exact settlement boundaries.
    const periods = p.days * 24 / p.intervalHours;
    const nearest = Math.round(periods);
    const settlements = Math.floor(Math.abs(periods - nearest) <=
      Number.EPSILON * Math.max(1, Math.abs(periods)) * 4 ? nearest : periods);
    if (!Number.isSafeInteger(settlements)) throw new RangeError('Holding period is too large');
    const fundingPerSettlement = notional * p.fundingRate / 100;
    const fundingIncome = fundingPerSettlement * settlements;
    const totalFees = notional * (p.spotOpen + p.spotClose + p.perpOpen + p.perpClose) / 100;
    const netProfit = fundingIncome - totalFees;
    const roi = netProfit / p.principal;
    const apr = p.days > 0 ? roi * 365 / p.days : null;
    const rawApy = p.days > 0 && roi > -1 ? Math.expm1(Math.log1p(roi) * 365 / p.days) : null;
    const apy = rawApy !== null && Number.isFinite(rawApy) ? rawApy : null;
    const ratio = totalFees / fundingPerSettlement;
    const breakEvenSettlements = totalFees === 0 ? 0 : fundingPerSettlement > 0
      ? Math.ceil(ratio - Number.EPSILON * Math.max(1, Math.abs(ratio)) * 4) : null;
    const breakEvenDays = breakEvenSettlements === null ? null : breakEvenSettlements * p.intervalHours / 24;
    const result = { notional, grossExposure: 2 * notional, spotCapital, margin,
      settlements, fundingPerSettlement, fundingIncome, totalFees, netProfit,
      roi, apr, apy, breakEvenDays, breakEvenSettlements };
    if (Object.values(result).some(v => v !== null && !Number.isFinite(v)))
      throw new RangeError('Inputs exceed numeric limits');
    return result;
  }
  if (typeof module === 'object' && module.exports) module.exports = { calculate };
  else root.FundingCalc = { calculate };
})(typeof globalThis !== 'undefined' ? globalThis : this);
