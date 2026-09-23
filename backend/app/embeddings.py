"""Compatibility fix for NVIDIAEmbedding 0.6.0 query mode/dimensions."""
from llama_index.embeddings.nvidia import NVIDIAEmbedding


class RetrievalEmbedding(NVIDIAEmbedding):
    def _get_query_embedding(self, query):
        # Upstream 0.6.0 sends passage mode for synchronous queries.
        extra = {"input_type": "query", "truncate": self.truncate}
        if self.dimensions:
            extra["dimensions"] = self.dimensions
        return self._client.embeddings.create(input=[query], model=self.model, extra_body=extra).data[0].embedding

    async def _aget_query_embedding(self, query):
        extra = {"input_type": "query", "truncate": self.truncate}
        if self.dimensions:
            extra["dimensions"] = self.dimensions
        response = await self._aclient.embeddings.create(input=[query], model=self.model, extra_body=extra)
        return response.data[0].embedding
