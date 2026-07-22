/**
 * Security Champion Dashboard — IBM watsonx AI Integration Helper
 *
 * This script demonstrates calling the IBM watsonx.ai foundation model API
 * (ibm/granite-3-8b-instruct) via the serve.py proxy (/api/watsonx).
 *
 * PRIMARY AI path (production):
 *   serve.py  /api/watsonx  →  us-south.ml.cloud.ibm.com/ml/v1/text/chat
 *   serve.py  /api/iam      →  IBM Cloud IAM token exchange
 *   serve.py  /api/ica      →  IBM Consulting Advantage REMEA agent
 *
 * Usage (browser / Node):
 *   const reply = await askWatsonx('Explain CWE-89 and show a Java fix');
 *   console.log(reply);
 */

const WATSONX_PROXY   = '/api/watsonx';
const WATSONX_MODEL   = 'ibm/granite-3-8b-instruct';

/**
 * Exchange an IBM Cloud API key for a short-lived IAM Bearer token.
 * @param {string} ibmApiKey — IBM Cloud API key (never logged or stored)
 * @returns {Promise<string>} Bearer token
 */
async function getIBMBearerToken(ibmApiKey) {
  const res = await fetch('/api/iam', {
    method:  'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body:    `grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=${encodeURIComponent(ibmApiKey)}`
  });
  if (!res.ok) throw new Error(`IAM token exchange failed: ${res.status}`);
  const data = await res.json();
  return data.access_token;
}

/**
 * Send a message to IBM watsonx.ai (ibm/granite-3-8b-instruct) via the proxy.
 * @param {string} userMessage   — The question or prompt
 * @param {string} bearerToken   — IBM Cloud IAM Bearer token
 * @param {string} [projectId]   — watsonx.ai project ID (optional)
 * @param {string} [region]      — IBM Cloud region (default: us-south)
 * @returns {Promise<string>}    — The model's text response
 */
async function askWatsonx(userMessage, bearerToken, projectId = '', region = 'us-south') {
  const payload = {
    model_id: WATSONX_MODEL,
    messages: [
      {
        role:    'system',
        content: 'You are an IBM security expert. Provide concise, actionable vulnerability remediation guidance with code examples.'
      },
      {
        role:    'user',
        content: userMessage
      }
    ],
    parameters: {
      max_new_tokens: 1024,
      temperature:    0.3
    },
    ...(projectId ? { project_id: projectId } : {})
  };

  const res = await fetch(WATSONX_PROXY, {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${bearerToken}`,
      'X-Model-Id':    WATSONX_MODEL,
      'X-Project-Id':  projectId,
      'X-Region':      region
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`watsonx.ai error ${res.status}: ${err}`);
  }

  const data = await res.json();
  // Granite returns choices[0].message.content or results[0].generated_text
  return (
    data?.choices?.[0]?.message?.content ||
    data?.results?.[0]?.generated_text   ||
    JSON.stringify(data)
  );
}

// Export for Node.js / ES module environments
if (typeof module !== 'undefined') {
  module.exports = { askWatsonx, getIBMBearerToken };
}
