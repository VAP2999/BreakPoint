export const PRICE = 2400;
export function total(quantity, fixed) { return quantity === 0 && !fixed ? PRICE : PRICE * quantity; }
export function expectedTotal(quantity) { return PRICE * quantity; }
export function evidence(quantity, fixed) {
 const actual = total(quantity, fixed), expected = expectedTotal(quantity);
 return {scenario:'Remove the last item', quantity, actualCents:actual, expectedCents:expected, confirmed:actual!==expected, mode:fixed?'fixed':'seeded-bug', source:'deterministic fixture probe; not AI discovery'};
}
