export function fmt(value?: string | null) {
  if (!value) return "Not recorded";
  return value.slice(0, 10);
}

export function humanize(value?: string | null) {
  return (value ?? "Not recorded").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
