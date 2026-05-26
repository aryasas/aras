import { expect, test, type Page } from '@playwright/test'

const publicPlans = [
  {
    id: 1,
    plan_key: 'free',
    name: 'Free',
    price: 0,
    currency: 'IDR',
    max_users: 1,
    max_branches: 1,
    max_transactions: 50,
    max_products: 30,
    api_access: false,
    active_modules: ['pos'],
    features: { included: ['Modul POS', '50 transaksi/bulan'] },
  },
  {
    id: 2,
    plan_key: 'lite',
    name: 'Lite',
    price: 50000,
    currency: 'IDR',
    max_users: 3,
    max_branches: 1,
    max_transactions: -1,
    max_products: 500,
    api_access: false,
    active_modules: ['pos', 'stock', 'receivable'],
    features: { included: ['Modul POS + Stok + Hutang Piutang'] },
  },
  {
    id: 3,
    plan_key: 'growth',
    name: 'Growth',
    price: 299000,
    currency: 'IDR',
    max_users: 10,
    max_branches: 2,
    max_transactions: -1,
    max_products: -1,
    api_access: false,
    active_modules: ['pos', 'stock', 'receivable', 'accounting'],
    features: { included: ['Semua fitur Lite'] },
  },
  {
    id: 4,
    plan_key: 'business',
    name: 'Business',
    price: 599000,
    currency: 'IDR',
    max_users: 25,
    max_branches: -1,
    max_transactions: -1,
    max_products: -1,
    api_access: true,
    active_modules: ['pos', 'stock', 'receivable', 'accounting'],
    features: { included: ['Semua fitur Growth'] },
  },
  {
    id: 99,
    plan_key: 'enterprise',
    name: 'Enterprise',
    price: 999000,
    currency: 'IDR',
    max_users: 99,
    max_branches: -1,
    max_transactions: -1,
    max_products: -1,
    api_access: true,
    active_modules: ['crm'],
    features: { included: ['Hidden legacy plan'] },
  },
]

async function mockPublicPlans(page: Page) {
  await page.route('**/api/v1/saas/plans/public', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(publicPlans),
    })
  })
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  expect(overflow).toBeLessThanOrEqual(1)
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('aras_lang', 'id')
  })
  await mockPublicPlans(page)
})

test('public landing filters pricing and switches EN/ID cleanly', async ({ page }) => {
  await page.goto('/welcome')

  await expect(page.getByRole('heading', { name: /kelola bisnis lebih mudah/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Free' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Lite' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Growth' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Business' })).toBeVisible()
  await expect(page.getByText('Enterprise', { exact: true })).toHaveCount(0)
  await expectNoHorizontalOverflow(page)

  await page.getByRole('button', { name: 'EN' }).click()
  await expect(page.getByRole('heading', { name: /run your business more easily/i })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Start Free' }).first()).toHaveAttribute('href', '/signup?plan=free')
  await expect(page.getByRole('link', { name: 'Start Now' }).first()).toHaveAttribute('href', '/signup?plan=lite')
  await expectNoHorizontalOverflow(page)
})

test('signup preselects plan_key from query and localizes labels', async ({ page }) => {
  await page.goto('/signup?plan=growth')

  await expect(page.getByRole('heading', { name: 'Daftar ARAS' })).toBeVisible()
  await expect(page.locator('#plan_key')).toHaveValue('growth')
  await expect(page.getByText('Paket Dipilih')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Growth' })).toBeVisible()
  await expect(page.locator('#plan_key option')).toHaveCount(5)
  await expect(page.locator('#plan_key option[value="enterprise"]')).toHaveCount(0)
  await expectNoHorizontalOverflow(page)

  await page.getByRole('button', { name: 'EN' }).click()
  await expect(page.getByRole('heading', { name: 'Sign up for ARAS' })).toBeVisible()
  await expect(page.getByLabel('Choose Plan')).toHaveValue('growth')
  await expectNoHorizontalOverflow(page)
})
