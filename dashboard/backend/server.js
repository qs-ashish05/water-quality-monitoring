import 'dotenv/config';
import express from 'express';
import pg from 'pg';

const PORT = process.env.PORT || 4000;
const DEFAULT_LIMIT = 10;
const MAX_LIMIT = 500;

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL is missing. Copy .env.example to .env and fill it in.');
  process.exit(1);
}

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }, // Supabase requires SSL
  max: 5,
});

// pg returns NUMERIC columns as strings, so convert them to numbers for the UI
const NUMERIC_COLUMNS = ['temperature', 'conductivity', 'ph', 'colour', 'dissolved_oxygen'];

const app = express();

// GET /api/readings?limit=10  ->  latest N rows, oldest first (ready for charting)
app.get('/api/readings', async (req, res) => {
  const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || DEFAULT_LIMIT, 1), MAX_LIMIT);

  try {
    const { rows } = await pool.query(
      `SELECT *
         FROM (SELECT * FROM water_quality ORDER BY generated_at DESC LIMIT $1) AS latest
        ORDER BY generated_at ASC`,
      [limit]
    );

    res.json(
      rows.map((row) => {
        const out = { ...row };
        for (const col of NUMERIC_COLUMNS) {
          out[col] = row[col] === null ? null : Number(row[col]);
        }
        return out;
      })
    );
  } catch (err) {
    console.error('Query failed:', err.message);
    res.status(500).json({ error: 'Failed to read from the database' });
  }
});

app.get('/api/health', (_req, res) => res.json({ ok: true }));

app.listen(PORT, () => {
  console.log(`Water quality API listening on http://localhost:${PORT}`);
});
