import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseStream } from './stream.js'

test('every trailer boundary preserves the answer and final sources', () => {
  const answer = 'The launch code is cobalt-orchid-731.'
  const sources = [{index: 1, file_name: 'fixture.pdf', snippet: 'Launch code'}]
  const trailer = '|||SOURCES|||' + JSON.stringify(sources)
  for (let at = 1; at < trailer.length; at++) {
    const partial = parseStream(answer + trailer.slice(0, at))
    assert.equal(partial.content, answer)
  }
  assert.deepEqual(parseStream(answer + trailer, true), {content: answer, sources})
})

test('a disconnected response cannot be mistaken for successful completion', () => {
  assert.throws(() => parseStream('partial answer', true))
  assert.throws(() => parseStream('answer|||SOURCES|||[{', true))
})
