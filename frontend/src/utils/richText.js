export function parseRichText(text) {
  if (!text) return []
  const tokens = []
  const regex = /(\*\*[^*]+\*\*)|(\*[^*]+\*)|(`[^`]+`)|(https?:\/\/[^\s]+)/g
  let lastIndex = 0
  let match
  while ((match = regex.exec(text))) {
    if (match.index > lastIndex) {
      tokens.push({ type: 'text', value: text.slice(lastIndex, match.index) })
    }
    const m = match[0]
    if (m.startsWith('**')) tokens.push({ type: 'bold', value: m.slice(2, -2) })
    else if (m.startsWith('`')) tokens.push({ type: 'code', value: m.slice(1, -1) })
    else if (m.startsWith('*')) tokens.push({ type: 'italic', value: m.slice(1, -1) })
    else tokens.push({ type: 'link', value: m })
    lastIndex = regex.lastIndex
  }
  if (lastIndex < text.length) tokens.push({ type: 'text', value: text.slice(lastIndex) })
  return tokens
}
