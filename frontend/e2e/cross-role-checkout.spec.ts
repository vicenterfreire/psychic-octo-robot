import { expect, test, type Page } from '@playwright/test'

const eventName = 'Aurora Live 2030'
const updatedVenue = 'Gather Hall E2E'

type SeededRole = 'Organizer' | 'Customer' | 'Gate'

async function loginAs(page: Page, role: SeededRole) {
  await page.goto('/login')
  await page.getByRole('button', { name: role, exact: true }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
}

async function signOut(page: Page) {
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
}

test('organizer changes reach customer checkout and one-time gate validation', async ({ page }) => {
  await test.step('Organizer updates the published event', async () => {
    await loginAs(page, 'Organizer')
    await expect(page.getByRole('heading', { name: 'Drafts and published events' })).toBeVisible()

    const managedEvent = page
      .getByRole('article')
      .filter({ has: page.getByRole('heading', { name: eventName, level: 3 }) })
    await managedEvent.getByRole('button', { name: 'Edit', exact: true }).click()
    await managedEvent.getByLabel('Venue').fill(updatedVenue)
    await managedEvent.getByRole('button', { name: 'Save changes', exact: true }).click()
    await expect(managedEvent).toContainText(updatedVenue)
    await signOut(page)
  })

  let ticketToken = ''
  await test.step('Customer reserves, approves, and opens the issued ticket', async () => {
    await loginAs(page, 'Customer')
    const eventCard = page
      .getByRole('article')
      .filter({ has: page.getByRole('heading', { name: eventName, level: 2 }) })
    await expect(eventCard).toContainText(updatedVenue)
    await eventCard.getByRole('link', { name: 'View event' }).click()

    await page.getByRole('button', { name: 'Hold 1 ticket' }).click()
    await expect(page.getByRole('heading', { name: eventName })).toBeVisible()
    await page.getByRole('button', { name: 'Simulate approval' }).click()
    await expect(page.getByRole('heading', { name: 'Your tickets are issued.' })).toBeVisible()
    await page.getByRole('link', { name: 'Open my tickets' }).click()

    const sharedTicketLink = page.getByRole('link', { name: 'Open shared view' }).first()
    const shareUrl = await sharedTicketLink.getAttribute('href')
    expect(shareUrl).not.toBeNull()
    ticketToken = decodeURIComponent(new URL(shareUrl!).pathname.split('/').at(-1) ?? '')
    expect(ticketToken).toMatch(/^v1\.[0-9a-f]{32}\.[A-Za-z0-9_-]+$/)
    await signOut(page)
  })

  await test.step('Gate accepts the ticket exactly once', async () => {
    await loginAs(page, 'Gate')
    await expect(page.getByLabel('Event')).toContainText(`${eventName} — ${updatedVenue}`)

    await page.getByLabel('Ticket code').fill(ticketToken)
    await page.getByRole('button', { name: 'Validate ticket' }).click()
    await expect(page.getByRole('heading', { name: 'Entry approved' })).toBeVisible()

    await page.getByLabel('Ticket code').fill(ticketToken)
    await page.getByRole('button', { name: 'Validate ticket' }).click()
    await expect(page.getByRole('heading', { name: 'Already used' })).toBeVisible()
  })
})
