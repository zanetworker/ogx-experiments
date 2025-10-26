import os
import asyncio
import httpx
from termcolor import cprint
from llama_stack_client import LlamaStackClient
from openai import OpenAI

async def fetch_document_content(url):
    """Fetch document content from URL"""
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url)
        if response.status_code == 200:
            return response.text
    return ""

def simple_chunk_text(text, chunk_size=2048, overlap=200):
    """Simple text chunking by character count"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append(chunk_text)
        start = end - overlap if end < text_len else end
    
    return chunks

async def main():
    # Initialize Llama Stack client
    port = os.environ.get('LLAMA_STACK_PORT', '8321')
    llama_client = LlamaStackClient(
        base_url=f"http://localhost:{port}"
    )

    # Initialize OpenAI client for chat completions
    openai_client = OpenAI(
        base_url=f"http://localhost:{port}/v1/openai/v1",
        api_key="dummy-key"  # Llama Stack doesn't check this
    )

    cprint(f"Connected to Llama Stack at http://localhost:{port}", "cyan")
    
    # Documents to be used for RAG
    urls = ["chat.rst", "llama3.rst", "datasets.rst", "lora_finetune.rst"]
    base_url = "https://raw.githubusercontent.com/pytorch/torchtune/main/docs/source/tutorials/"
    
    cprint("Fetching documents from URLs...", "cyan")
    documents = []
    for i, url in enumerate(urls):
        full_url = f"{base_url}{url}"
        cprint(f"  Fetching {url}...", "yellow")
        content = await fetch_document_content(full_url)
        if content:
            documents.append({
                "document_id": f"num-{i}",
                "url": full_url,
                "content": content
            })
            cprint(f"    ✓ Loaded {len(content)} chars", "green")
    
    # Upload files first
    cprint("\nUploading files...", "cyan")
    file_ids = []

    for doc in documents:
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(doc["content"])
            temp_path = f.name

        try:
            # Upload the file
            with open(temp_path, 'rb') as f:
                file_response = llama_client.files.create(
                    file=f,
                    purpose='assistants'
                )
                file_ids.append(file_response.id)
                cprint(f"  ✓ Uploaded {doc['document_id']}: {file_response.id}", "green")
        finally:
            # Clean up temp file
            import os as os_module
            os_module.unlink(temp_path)

    # Create vector store with files
    import time
    vector_store_name = f"test-vector-store-{int(time.time())}"  # Unique name each time
    cprint(f"\nCreating vector store '{vector_store_name}' with {len(file_ids)} files...", "cyan")

    try:
        # Don't specify embedding model in metadata - let it use the default from server config
        vector_store = llama_client.vector_stores.create(
            name=vector_store_name,
            file_ids=file_ids,
            metadata={
                "description": "PyTorch documentation"
            }
        )
        vector_store_id = vector_store.id
        cprint(f"  ✓ Created vector store: {vector_store_id}", "green")
    except Exception as e:
        cprint(f"  Error creating vector store: {e}", "red")
        raise

    # Wait for files to be processed
    cprint("\nWaiting for files to be processed...", "cyan")
    import time
    max_wait = 60  # Maximum wait time in seconds
    wait_interval = 2  # Check every 2 seconds
    elapsed = 0

    while elapsed < max_wait:
        # Check vector store status
        vs_status = llama_client.vector_stores.retrieve(vector_store_id=vector_store_id)
        if vs_status.file_counts.completed == len(file_ids):
            cprint(f"  ✓ All {len(file_ids)} files processed successfully!", "green")
            break
        elif vs_status.file_counts.failed > 0:
            cprint(f"  ⚠ {vs_status.file_counts.failed} files failed to process", "yellow")
            # List the files to see what went wrong
            files_list = llama_client.vector_stores.files.list(vector_store_id=vector_store_id)
            for file in files_list.data:
                if file.status == "failed" and file.last_error:
                    cprint(f"    File {file.id}: {file.last_error.message}", "red")
            break
        else:
            in_progress = vs_status.file_counts.in_progress
            completed = vs_status.file_counts.completed
            cprint(f"  Processing... ({completed}/{len(file_ids)} completed, {in_progress} in progress)", "yellow")
            time.sleep(wait_interval)
            elapsed += wait_interval

    if elapsed >= max_wait:
        cprint(f"  ⚠ Timeout waiting for files to process", "yellow")
    
    # Query using vector store search directly
    prompt = "What are the top 5 topics that were explained? Only list succinct bullet points."

    cprint(f"\n{'='*80}", "cyan")
    cprint(f"User> {prompt}", "green")
    cprint(f"{'='*80}", "cyan")

    # First, search the vector store to retrieve relevant context
    cprint("\nSearching vector store for relevant context...", "cyan")
    search_result = llama_client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=prompt,
        max_num_results=5,
        search_mode="vector"
    )

    # Display retrieved chunks
    cprint(f"\n✓ Retrieved {len(search_result.data)} relevant chunks:", "green")
    context_text = ""
    for i, result in enumerate(search_result.data, 1):
        cprint(f"\n  Chunk {i} (score: {result.score:.3f}):", "yellow")
        preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
        print(f"    {preview}")
        context_text += f"\n\nChunk {i}:\n{result.content}"

    # Now use the context with OpenAI client to generate answer
    cprint("\n\nGenerating answer using retrieved context...", "cyan")

    # Build the prompt with context
    full_prompt = f"""Based on the following context from PyTorch documentation, {prompt}

Context:
{context_text}

Answer:"""

    # Use OpenAI-compatible chat completions API
    response = openai_client.chat.completions.create(
        model=os.environ.get("INFERENCE_MODEL", "ollama/llama3.2:3b-instruct-fp16"),
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant specialized in analyzing PyTorch documentation. Provide clear, concise answers based on the given context."
            },
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        stream=False
    )

    # Display the response
    cprint("\nAssistant>", "blue")
    print(response.choices[0].message.content)

    cprint(f"\n{'='*80}", "cyan")
    cprint("✓ Query completed successfully", "green")

if __name__ == "__main__":
    asyncio.run(main())