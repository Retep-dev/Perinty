import dotenv
dotenv.load_dotenv()
from app.rag import ingest_document, generate_streaming_response, clear_storage

print("Clearing storage...")
clear_storage()

print("Ingesting test document...")
with open("test_kb.txt", "r") as f:
    text = f.read()

res = ingest_document("test_kb.txt", text)
print("Ingestion Result:", res)

print("Querying RAG...")
response_gen = generate_streaming_response("What is Perinty?")
for chunk in response_gen:
    print(chunk, end="")
print("\nDone!")
