'use strict';
const assert = require('node:assert/strict');
const { calculate } = require('./calc.js');
let passed = 0;
function test(name, fn) { fn(); passed++; console.log(`✓ ${name}`); }
function near(actual, expected) {
  assert.ok(Math.abs(actual - expected) <= 1e-10 * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
}
test('Default allocation, funding, fees, ROI, APR and break-even', () => {
  const r = calculate({});
  near(r.notional, 7500); near(r.spotCapital, 7500); near(r.margin, 2500);
  near(r.grossExposure, 15000); assert.equal(r.settlements, 90);
  near(r.fundingIncome, 67.5); near(r.totalFees, 22.5); near(r.netProfit, 45);
  near(r.roi, 0.0045); near(r.apr, 0.05475); near(r.breakEvenDays, 10);
  near(r.apy, Math.pow(1.0045, 365 / 30) - 1);
});
test('1× leverage splits principal evenly', () => {
  const r = calculate({ principal: 2000, leverage: 1 });
  near(r.notional, 1000); near(r.margin, 1000); near(r.netProfit, 6);
});
test('All four fee directions are charged separately', () => {
  const r = calculate({ spotOpen: 0.1, spotClose: 0.2, perpOpen: 0.3, perpClose: 0.4 });
  near(r.totalFees, 75); near(r.netProfit, -7.5);
});
test('Negative funding costs the short and cannot recover fees', () => {
  const r = calculate({ fundingRate: -0.01 });
  near(r.fundingIncome, -67.5); near(r.netProfit, -90);
  assert.equal(r.breakEvenDays, null); assert.ok(r.apr < 0 && r.apy < 0);
});
test('Zero funding with fees never breaks even', () => {
  const r = calculate({ fundingRate: 0 });
  near(r.netProfit, -22.5); assert.equal(r.breakEvenDays, null);
});
test('Zero fees break even immediately', () => {
  const r = calculate({ fundingRate: 0, spotOpen: 0, spotClose: 0, perpOpen: 0, perpClose: 0 });
  near(r.totalFees, 0); near(r.netProfit, 0); assert.equal(r.breakEvenDays, 0);
});
test('Only complete settlements count, including exact boundaries', () => {
  assert.equal(calculate({ days: 7.99 / 24 }).settlements, 0);
  assert.equal(calculate({ days: 8 / 24 }).settlements, 1);
  assert.equal(calculate({ days: 15.99 / 24 }).settlements, 1);
  assert.equal(calculate({ days: 16 / 24 }).settlements, 2);
  assert.equal(calculate({ days: 0.3 / 24, intervalHours: 0.1 }).settlements, 3);
});
test('Zero holding days still pays round-trip fees; annualization unavailable', () => {
  const r = calculate({ days: 0 });
  assert.equal(r.settlements, 0); near(r.netProfit, -22.5);
  assert.equal(r.apr, null); assert.equal(r.apy, null);
});
test('Break-even rounds up to the next settlement', () => {
  const r = calculate({ fundingRate: 0.07 });
  assert.equal(r.breakEvenSettlements, 5); near(r.breakEvenDays, 5 / 3);
  assert.ok(r.fundingPerSettlement * 4 < r.totalFees);
  assert.ok(r.fundingPerSettlement * 5 >= r.totalFees);
});
test('APY is unavailable for losses of 100% or more', () => {
  assert.equal(calculate({ fundingRate: -10 }).apy, null);
});
test('Invalid, empty-like and overflowing numeric inputs are rejected', () => {
  for (const input of [{principal:0},{principal:-1},{leverage:0.9},{intervalHours:0},
    {days:-1},{spotOpen:-0.1},{spotClose:-1},{perpOpen:-1},{perpClose:-1},
    {fundingRate:NaN},{principal:Infinity},{days:'30'},{days:null},
    {days:Number.MAX_VALUE},{principal:Number.MAX_VALUE}]) {
    assert.throws(() => calculate(input), RangeError);
  }
});
test('Pure function preserves inputs and returns repeatable results', () => {
  const input = Object.freeze({ principal: 4321, leverage: 2.5, days: 14.5 });
  assert.deepEqual(calculate(input), calculate(input));
  const r = calculate(input);
  near(r.spotCapital + r.margin, input.principal);
  near(r.margin * input.leverage, r.notional);
});
console.log(`\n${passed} tests passed.`);
