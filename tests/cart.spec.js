import {test,expect} from '@playwright/test';
for (const fixed of [false,true]) {
 test(`empty cart contract: ${fixed?'fixed control':'seeded bug'}`, async ({page})=>{
  test.fail(!fixed,'Intentional fixture bug: empty cart keeps $24 total');
  await page.goto(`/?mode=${fixed?'fixed':'buggy'}`);
  await page.getByRole('button',{name:'Remove item'}).click();
  await expect(page.getByTestId('quantity')).toHaveText('0');
  await expect(page.getByTestId('total')).toHaveText('$0.00');
 });
}
