// Local development adapter. No credentials or model API keys belong here.
const API_BASE = 'http://localhost:8000/api';

async function request(path, body) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw new Error('Cannot reach the API or request timed out. Check the backend on localhost:8000. A timed-out action may have completed; refresh the audit log before retrying.');
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === 'string' ? payload.detail
      : Array.isArray(payload.detail) ? payload.detail.map(item => item.msg).join('; ')
        : `API request failed (${response.status}).`;
    throw new Error(detail);
  }
  return response.json();
}

export const api = {
  users: () => request('/users'),
  events: () => request('/events'),
  chat: (customerId, message) => request('/chat', { customer_id: customerId, message }),
  attack: (customerId, targetId) => request('/attacks', {
    customer_id: customerId, target_customer_id: targetId,
  }),
};
