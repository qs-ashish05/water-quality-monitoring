// ---------------------------------------------------------------------------
// Dashboard configuration
// ---------------------------------------------------------------------------

// Sliding window: how many of the latest rows feed the averages and the graph.
// Change via VITE_WINDOW_SIZE in .env, or use the dropdown in the UI.
export const DEFAULT_WINDOW = Number(import.meta.env.VITE_WINDOW_SIZE) || 10;
export const WINDOW_OPTIONS = [5, 10, 20, 30, 60];

// How often the dashboard re-reads the database (ms).
export const REFRESH_MS = Number(import.meta.env.VITE_REFRESH_MS) || 6000;

// ---------------------------------------------------------------------------
// Parameters and their SAFE ranges.
//
// These match how the sensor API flags values in your sample data
// (e.g. 25.95 °C and 4.07 mg/L DO were both flagged "safe: false"):
//   - Temperature: safe only inside the desirable 20–25 °C band
//   - EC:          safe up to the permissible limit of 3000 µS/cm
//   - pH:          6.5 – 8.5
//   - Colour:      safe up to the permissible limit of 15 Hazen
//   - DO:          safe at >= 6 mg/L
// To be more lenient (e.g. treat 25–30 °C as safe) just edit the numbers below.
// ---------------------------------------------------------------------------
export const PARAMS = [
  {
    key: 'temperature',
    safeKey: 'temperature_safe',
    tagKey: 'temperature_tag',
    label: 'Temperature',
    avgLabel: 'Avg temperature',
    unit: '°C',
    decimals: 2,
    safe: { min: 20, max: 25 },
  },
  {
    key: 'conductivity',
    safeKey: 'conductivity_safe',
    tagKey: 'conductivity_tag',
    label: 'EC',
    avgLabel: 'Avg EC',
    unit: 'µS/cm',
    decimals: 2,
    safe: { min: 0, max: 3000 },
  },
  {
    key: 'ph',
    safeKey: 'ph_safe',
    tagKey: 'ph_tag',
    label: 'pH level',
    avgLabel: 'Avg pH level',
    unit: 'pH',
    decimals: 2,
    safe: { min: 6.5, max: 8.5 },
  },
  {
    key: 'colour',
    safeKey: 'colour_safe',
    tagKey: 'colour_tag',
    label: 'Colour indicator',
    avgLabel: 'Avg colour indicator',
    unit: 'Hazen',
    decimals: 2,
    safe: { min: 0, max: 15 },
  },
  {
    key: 'dissolved_oxygen',
    safeKey: 'do_safe',
    tagKey: 'do_tag',
    label: 'Oxygen level',
    avgLabel: 'Avg oxygen level',
    unit: 'mg/L',
    decimals: 2,
    safe: { min: 6 }, // no upper limit
  },
];

/** Returns true / false, or null when there is no value. */
export function isSafe(param, value) {
  if (value === null || value === undefined) return null;
  const { min = -Infinity, max = Infinity } = param.safe;
  return value >= min && value <= max;
}
