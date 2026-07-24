from app.rag import get_index, list_documents
import dotenv
dotenv.load_dotenv()


print("Documents in Supabase:")
print(list_documents())

idx = get_index()

# Ask something related to YOUR document
question = "What are the types of economic structure?"

query_engine = idx.as_query_engine(similarity_top_k=4)
response = query_engine.query(question)

print(f"\nQuestion: {question}")
print(f"Number of source nodes retrieved: {len(response.source_nodes)}")

print("\nRetrieved source nodes:")
for i, node in enumerate(response.source_nodes):
    print(f"{i+1}. {node.node.metadata.get('file_name')} | score: {node.score:.3f}")
    print(node.node.get_content()[:300])

print("\nLLM response:")
print(repr(response.response))
