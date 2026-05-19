import { expect, test } from '@playwright/test';

test.describe('TrongkAI - smoke del flujo crítico', () => {
  test('home muestra dashboard operacional y suppliers', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Dashboard operacional' })).toBeVisible();
    await expect(page.getByText('Olivero 1')).toBeVisible();
    await expect(page.getByText('Olivero 3')).toBeVisible();
  });

  test('nav lleva a las 7 secciones', async ({ page }) => {
    await page.goto('/');
    for (const label of ['Operacional', 'Agenda camiones', 'Balance de masa', 'Plan 5 años', 'What-if', 'Supuestos', 'Equipo']) {
      await expect(page.getByRole('link', { name: label })).toBeVisible();
    }
  });

  test('about muestra liderazgo y directorio', async ({ page }) => {
    await page.goto('/about');
    await expect(page.getByRole('heading', { name: /Innovación en Nutrición Circular/i })).toBeVisible();
    await expect(page.getByText('José Cuevas')).toBeVisible();
    await expect(page.getByText('Jaime Echeverría')).toBeVisible();
    await expect(page.getByText('Guido Rietta')).toBeVisible();
  });

  test('supuestos muestra contador de PDs', async ({ page }) => {
    await page.goto('/supuestos');
    await expect(page.getByText(/PD activos/)).toBeVisible();
  });

  test('whatif renderiza botón de simulación', async ({ page }) => {
    await page.goto('/whatif');
    await expect(page.getByRole('button', { name: /Ejecutar 5 escenarios/i })).toBeVisible();
  });
});
