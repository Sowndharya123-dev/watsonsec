/**
 * Security Champion — Vulnerability Remediation Dashboard
 * Express static server
 *
 * ── AI Integration Architecture ─────────────────────────────────────────────
 *
 *  PRIMARY (IBM watsonx.ai + ICA):
 *    serve.py  /api/watsonx  →  us-south.ml.cloud.ibm.com/ml/v1/text/chat
 *                                model: ibm/granite-3-8b-instruct
 *    serve.py  /api/iam      →  iam.cloud.ibm.com (IBM Cloud IAM token exchange)
 *    serve.py  /api/ica      →  remea.ica.ibm.com  (IBM Consulting Advantage agent)
 *
 *  LOCAL DEV FALLBACK (Anthropic Claude — not used in production / IBM Cloud):
 *    This file  /api/chat   →  api.anthropic.com/v1/messages
 *    Set ANTHROPIC_API_KEY in .env for local testing only.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * Credentials live ONLY on the server — never sent to the browser.
 *
 * Local dev: create a .env file in the project root:
 *   ANTHROPIC_API_KEY=sk-ant-...
 */
const express = require('express');
const path    = require('path');
const fs      = require('fs');

// ── Load .env if present (no extra package needed) ──────────────────────────
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf8').split('\n').forEach(line => {
    const [k, ...rest] = line.split('=');
    if (k && rest.length && !process.env[k.trim()]) {
      process.env[k.trim()] = rest.join('=').trim();
    }
  });
}

const app  = express();
const PORT = process.env.PORT || 3000;

// ── LOCAL DEV FALLBACK ONLY — production uses serve.py /api/watsonx (ibm/granite-3-8b-instruct) ──
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || '';
const ANTHROPIC_MODEL   = 'claude-sonnet-4-5';  // local-dev fallback — NOT the IBM watsonx path
const ANTHROPIC_URL     = 'https://api.anthropic.com/v1/messages';

app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, '..', 'public')));

// ── /api/chat ────────────────────────────────────────────────────────────────
// Accepts { messages: [{role, content}], system: string }
// Translates to Anthropic Messages API format — API key never leaves the server.
app.post('/api/chat', async (req, res) => {
  if (!ANTHROPIC_API_KEY) {
    return res.status(503).json({ error: 'AI not configured — set ANTHROPIC_API_KEY on the server.' });
  }

  try {
    // Separate system message from the conversation messages
    const allMessages = req.body.messages || [];
    const systemMsg   = allMessages.find(m => m.role === 'system')?.content || '';
    const chatMsgs    = allMessages.filter(m => m.role !== 'system');

    const anthropicRes = await fetch(ANTHROPIC_URL, {
      method:  'POST',
      headers: {
        'Content-Type':      'application/json',
        'x-api-key':         ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model:      ANTHROPIC_MODEL,
        max_tokens: 1024,
        system:     systemMsg,
        messages:   chatMsgs
      })
    });

    const data = await anthropicRes.json();

    if (!anthropicRes.ok) {
      return res.status(anthropicRes.status).json({ error: data?.error?.message || JSON.stringify(data) });
    }

    // Normalise to the shape the frontend already expects
    const text = data.content?.[0]?.text || '';
    res.json({ choices: [{ message: { content: text } }] });

  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});

// Health-check (IBM Cloud / CF expects this)
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'security-champion-dashboard', timestamp: new Date().toISOString() });
});

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Security Champion Dashboard running on port ${PORT}`);
  if (!ANTHROPIC_API_KEY) {
    console.warn('⚠  ANTHROPIC_API_KEY not set — /api/chat will return 503');
  } else {
    console.log(`✅ Claude claude-sonnet-4-5 Sonnet ready`);
  }
});

module.exports = app;
