import os
import asyncio
import httpx
from termcolor import cprint
from openai import OpenAI

async def fetch_document_content(url):
    """Fetch document content from URL"""
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url)
        if response.status_code == 200:
            return response.text
    return ""

async def main():
    # Initialize OpenAI client for Llama Stack
    port = os.environ.get('LLAMA_STACK_PORT', '8321')
    client = OpenAI(
        base_url=f"http://localhost:{port}/v1",
        api_key="not-needed"
    )

    cprint(f"Connected to Llama Stack at http://localhost:{port}", "cyan")

    # Create a simple vector store first (without files)
    cprint("\nCreating vector store...", "cyan")
    
    import time
    vector_store_name = f"pytorch-docs-{int(time.time())}"
    
    embedding_model = os.environ.get('EMBEDDING_MODEL', 'ollama/nomic-embed-text:latest')
    embedding_dim = 768

    # Use smaller chunk size to reduce load on embedding service
    chunk_size = int(os.environ.get('CHUNK_SIZE_IN_TOKENS', '256'))

    vector_store = client.vector_stores.create(
        name=vector_store_name,
        metadata={"description": "PyTorch documentation"},
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dim,
            "provider_id": "faiss",
            "chunking_strategy": {
                "type": "fixed",
                "chunk_size_in_tokens": chunk_size,
                "chunk_overlap_in_tokens": 0
            }
        }
    )
    vector_store_id = vector_store.id
    cprint(f"✓ Created vector store: {vector_store_id}", "green")

    # Fetch and process documents
    urls = ["chat.rst", "llama3.rst", "lora_finetune.rst"]
    base_url = "https://raw.githubusercontent.com/pytorch/torchtune/main/docs/source/tutorials/"

    cprint("\nFetching and uploading documents...", "cyan")
    file_ids = []
    
    for url in urls:
        full_url = f"{base_url}{url}"
        cprint(f"  Processing {url}...", "yellow")
        
        content = await fetch_document_content(full_url)
        if not content or len(content) < 100:
            cprint(f"    ✗ Skipped (empty or failed)", "red")
            continue
        
        cprint(f"    ✓ Fetched {len(content)} chars", "green")
        
        # Create file from content
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Upload file
            with open(temp_path, 'rb') as f:
                file_response = client.files.create(
                    file=f,
                    purpose='assistants'
                )
            file_id = file_response.id
            file_ids.append(file_id)
            cprint(f"    ✓ Uploaded: {file_id}", "green")

            # Attach to vector store with retry logic
            max_retries = 3
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    cprint(f"    ⏳ Attaching to vector store (attempt {attempt + 1}/{max_retries})...", "yellow")
                    client.vector_stores.files.create(
                        vector_store_id=vector_store_id,
                        file_id=file_id
                    )

                    # Wait longer for processing to avoid overwhelming the embedding service
                    cprint(f"    ⏳ Waiting for embedding generation...", "yellow")
                    time.sleep(retry_delay)

                    # Check status
                    vs_status = client.vector_stores.retrieve(vector_store_id=vector_store_id)
                    if vs_status.file_counts.completed > len(file_ids) - 1:
                        cprint(f"    ✓ File processed successfully!", "green")
                        break
                    elif vs_status.file_counts.failed > 0:
                        cprint(f"    ⚠ File may have failed to process", "yellow")
                        break
                    else:
                        cprint(f"    ⏳ Still processing...", "yellow")
                    break

                except Exception as attach_error:
                    if attempt < max_retries - 1:
                        cprint(f"    ⚠ Attachment failed (attempt {attempt + 1}), retrying in {retry_delay}s...", "yellow")
                        time.sleep(retry_delay)
                    else:
                        cprint(f"    ✗ Attachment failed after {max_retries} attempts: {attach_error}", "red")
                        raise

        except Exception as e:
            cprint(f"    ✗ Error: {e}", "red")
        finally:
            os.unlink(temp_path)

    # Wait for all files to finish processing
    cprint("\nWaiting for all files to complete processing...", "cyan")
    max_wait = 30
    for i in range(max_wait):
        vs_status = client.vector_stores.retrieve(vector_store_id=vector_store_id)
        completed = vs_status.file_counts.completed
        failed = vs_status.file_counts.failed
        in_progress = vs_status.file_counts.in_progress
        
        cprint(f"  Status: {completed} completed, {failed} failed, {in_progress} in progress", "yellow")
        
        if completed + failed >= len(file_ids):
            break
        
        time.sleep(1)
    
    if vs_status.file_counts.completed == 0:
        cprint("\n⚠ No files were successfully processed. This is a known issue with Llama Stack.", "yellow")
        cprint("The file processing may fail silently. Trying query anyway...", "yellow")

    # Query using Responses API
    prompt = "What are the top 5 topics that were explained? Only list succinct bullet points."

    cprint(f"\n{'='*80}", "cyan")
    cprint(f"User> {prompt}", "green")
    cprint(f"{'='*80}", "cyan")

    model = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o")
    cprint(f"\nUsing model: {model}", "yellow")

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            instructions="You are a helpful assistant specialized in analyzing PyTorch documentation. Provide clear, concise answers based on the retrieved context.",
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 5
            }],
            tool_choice="required",
            stream=False,
            include=["file_search_call.results"]
        )

        # Display file_search results
        for item in response.output:
            if item.type == "file_search_call":
                cprint(f"\n✓ File search completed with status: {item.status}", "green")
                if item.results:
                    cprint(f"  Retrieved {len(item.results)} chunks:", "yellow")
                    for i, result in enumerate(item.results[:3], 1):
                        chunk_text = result.text
                        preview = chunk_text[:150] + "..." if len(chunk_text) > 150 else chunk_text
                        cprint(f"\n  Chunk {i} (score: {result.score:.3f}):", "yellow")
                        print(f"    {preview}")

        # Display response
        cprint("\n\nAssistant>", "blue")
        print(response.output_text)

        cprint(f"\n{'='*80}", "cyan")
        cprint("✓ Query completed successfully", "green")
        
    except Exception as e:
        cprint(f"\n✗ Error during query: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

