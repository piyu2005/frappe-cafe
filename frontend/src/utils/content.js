// Posts written before the rich editor existed stored plain text with literal
// newlines. Wrap that as paragraphs so it still reads correctly once rendered
// through the HTML-based editor/viewer; content that's already HTML passes through.
export function ensureHtmlContent(raw) {
  if (!raw) return ''
  if (/<[a-z][\s\S]*>/i.test(raw)) return raw
  return raw
    .split(/\n{2,}/)
    .map((para) => `<p>${para.trim().replace(/\n/g, '<br>')}</p>`)
    .join('')
}
