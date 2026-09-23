const marker = '|||SOURCES|||'

export function parseStream(text, complete = false) {
  const at = text.indexOf(marker)
  if (at >= 0) {
    try {
      const sources = JSON.parse(text.slice(at + marker.length))
      if (!Array.isArray(sources)) throw new Error('Invalid sources')
      return { content: text.slice(0, at), sources }
    } catch {
      if (complete) throw new Error('The response ended before its sources arrived.')
      return { content: text.slice(0, at), sources: [] }
    }
  }
  if (complete) throw new Error('The response did not finish. Please try again.')
  // Network chunks may split the marker at any byte. Hold its possible prefix.
  for (let length = marker.length - 1; length > 0; length--) {
    if (text.endsWith(marker.slice(0, length))) {
      return { content: text.slice(0, -length), sources: [] }
    }
  }
  return { content: text, sources: [] }
}
