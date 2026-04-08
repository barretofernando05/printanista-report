export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const raw = await response.text();
  let data;
  try { data = JSON.parse(raw); } catch { throw new Error(raw || `Error HTTP ${response.status}`); }
  if (!response.ok) throw new Error(data.detail || "Error de API");
  return data;
}
