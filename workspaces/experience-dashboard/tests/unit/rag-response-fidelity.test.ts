import assert from 'node:assert/strict';
import test from 'node:test';
import { CACHED_RAG_QUESTIONS } from '../../src/features/rag-source/cachedAnswers';
import { api } from '../../src/shared/api/endpoints';
import { session } from '../../src/shared/api/session';

test('RAG keeps server sources and rejection for a previously cached question', async (t) => {
  const previousApiMode = process.env.NEXT_PUBLIC_API_MODE;
  process.env.NEXT_PUBLIC_API_MODE = 'live';
  session.set('fixture-access-token', new Date(Date.now() + 60_000).toISOString(), {
    userId: 'usr_fixture_user', username: 'fixture', role: 'USER',
  });
  t.after(() => {
    session.clear();
    if (previousApiMode === undefined) delete process.env.NEXT_PUBLIC_API_MODE;
    else process.env.NEXT_PUBLIC_API_MODE = previousApiMode;
  });

  const requestId = 'req_fixture_0000000000000000000000000000';
  const source = {
    citationId: 'cit_fixture',
    sourceId: 'src_fixture',
    title: 'Fixture source',
    canonicalUrl: 'https://example.org/source',
    citationKind: 'PUBLIC_WEB',
  };
  const responses = [
    { requestId, answerId: null, answer: null, generationStatus: 'RETRIEVAL_ONLY', citationCoverage: 1,
      citations: [source], retrievalFailure: false, guardrailFlags: [] },
    { requestId, answerId: null, answer: null, generationStatus: 'BLOCKED_SENSITIVE', citationCoverage: 0,
      citations: [], retrievalFailure: false, guardrailFlags: ['SENSITIVE_DATA_BLOCKED'] },
  ];
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(responses.shift()), {
    status: 200, headers: { 'Content-Type': 'application/json' },
  }));

  const request = { question: CACHED_RAG_QUESTIONS[0]!, answerMode: 'CONCISE' as const };
  const retrieved = await api.ragV2Ask(request);
  assert.equal(retrieved.generationStatus, 'RETRIEVAL_ONLY');
  assert.deepEqual(retrieved.citations, [source]);
  const blocked = await api.ragV2Ask(request);
  assert.equal(blocked.generationStatus, 'BLOCKED_SENSITIVE');
  assert.equal(blocked.answer, null);
});
