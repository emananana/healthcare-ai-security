// Local development adapter. No credentials or model API keys belong here.
const API_BASE = '/api';

async function request(path, body) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(45000),
    });
  } catch {
    throw new Error('Cannot reach the API or request timed out. The shared service may be waking up; wait a moment and refresh. For local development, check the backend terminal. A timed-out action may have completed; refresh the audit log before retrying.');
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
  status: () => request('/status'),
  users: () => request('/users'),
  events: () => request('/events'),
  chat: (customerId, message) => request('/chat', { customer_id: customerId, message }),
  attack: (customerId, targetId) => request('/attacks', {
    customer_id: customerId, target_customer_id: targetId,
  }),
};
