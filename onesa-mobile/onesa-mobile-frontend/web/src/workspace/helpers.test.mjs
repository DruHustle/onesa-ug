import test from 'node:test';
import assert from 'node:assert/strict';
import { usdMinor, makeRetryKeys, applicationState, stateTone, mergeRecordPage } from './helpers.mjs';

test('money input uses exact minor units and rejects excess precision or ambiguous amounts', () => {
  assert.equal(usdMinor('12.34'), 1234);
  assert.equal(usdMinor('0.01'), 1);
  assert.equal(usdMinor('100000.00'), 10000000);
  for (const value of ['0', '-1', '1.005', '1e3', '1,000', '100000.01', '']) assert.throws(() => usdMinor(value));
});
test('uncertain retries retain their request key; changed input and confirmed new requests get new keys', () => {
  let count = 0;
  const keys = makeRetryKeys(() => `request-${++count}`);
  const first = keys.get('POST /ledger', { amountMinor: 1234 });
  assert.equal(keys.get('POST /ledger', { amountMinor: 1234 }).key, first.key);
  assert.notEqual(keys.get('POST /ledger', { amountMinor: 1235 }).key, first.key);
  keys.confirmed(first.fingerprint);
  assert.notEqual(keys.get('POST /ledger', { amountMinor: 1234 }).key, first.key);
  keys.clear();
  assert.notEqual(keys.get('POST /ledger', { amountMinor: 1234 }).key, first.key);
});
test('application and financial labels never turn a pilot record into active service', () => {
  assert.match(applicationState('awaiting_host')[1], /Activation still needs/);
  assert.match(applicationState('information_required')[1], /update your application/);
  for (const state of ['test_recorded', 'test_refunded', 'planned', 'lab_simulator']) assert.equal(stateTone(state), 'neutral');
});
test('overlapping cursor pages preserve row identity and the latest record revision', () => {
  const current=[{id:'a',revision:3,state:'review_required'},{id:'b',revision:1}];
  const merged=mergeRecordPage(current,[{id:'a',revision:2,state:'information_required'},{id:'b',revision:2},{id:'c',revision:1}]);
  assert.deepEqual(merged.map(row=>row.id),['a','b','c']);
  assert.equal(merged[0].state,'review_required');
  assert.equal(merged[1].revision,2);
  assert.deepEqual(current,[{id:'a',revision:3,state:'review_required'},{id:'b',revision:1}]);
});
