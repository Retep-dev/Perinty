"""Diagnose Supabase pgvector/embedding insert issues."""
import dotenv

dotenv.load_dotenv()

from app.rag import supabase_client, Settings


def main():
    print("=" * 60)
    print("Supabase Vector Diagnostics")
    print("=" * 60)

    # 1. Basic connectivity
    print("\n1. Testing basic SELECT...")
    try:
        response = supabase_client.table("documents").select("id").limit(1).execute()
        print(f"   SELECT OK. Rows returned: {len(response.data)}")
    except Exception as e:
        print(f"   SELECT FAILED: {type(e).__name__}: {e}")

    # 2. Insert without embedding
    print("\n2. Testing INSERT without embedding...")
    try:
        response = supabase_client.table("documents").insert({
            "content": "diagnostic text no embedding",
            "metadata": {"test": True},
        }).execute()
        print(f"   INSERT (no embedding) OK. Rows: {len(response.data)}")
    except Exception as e:
        print(f"   INSERT (no embedding) FAILED: {type(e).__name__}: {e}")

    # 3. Generate embedding
    print("\n3. Testing NVIDIA embedding generation...")
    try:
        embedding = Settings.embed_model.get_text_embedding("diagnostic text")
        print(f"   Embedding OK. Dimension: {len(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"   Embedding FAILED: {type(e).__name__}: {e}")
        return

    # 4. Insert with embedding (raw RPC)
    print("\n4. Testing INSERT with embedding vector...")
    try:
        response = supabase_client.table("documents").insert({
            "content": "diagnostic text with embedding",
            "metadata": {"test": True},
            "embedding": embedding,
        }).execute()
        print(f"   INSERT (with embedding) OK. Rows: {len(response.data)}")
    except Exception as e:
        print(f"   INSERT (with embedding) FAILED: {type(e).__name__}: {e}")

    # 5. Check pgvector extension
    print("\n5. Checking pgvector extension...")
    try:
        response = supabase_client.table("pg_extension").select("extname, extversion").eq("extname", "vector").execute()
        print(f"   pgvector status: {response.data}")
    except Exception as e:
        print(f"   pg_extension query FAILED: {type(e).__name__}: {e}")

    # 6. Check documents table schema
    print("\n6. Checking documents table schema...")
    try:
        response = supabase_client.table("information_schema.columns").select("column_name, data_type, udt_name").eq("table_name", "documents").execute()
        print(f"   Schema: {response.data}")
    except Exception as e:
        print(f"   information_schema query FAILED: {type(e).__name__}: {e}")

    # 7. Check match_documents function
    print("\n7. Testing match_documents RPC...")
    try:
        response = supabase_client.rpc("match_documents", {
            "query_embedding": embedding,
            "match_threshold": 0.1,
            "match_count": 5,
        }).execute()
        print(f"   match_documents OK. Rows: {len(response.data)}")
    except Exception as e:
        print(f"   match_documents FAILED: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("Diagnostics complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
