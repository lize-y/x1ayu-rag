import os
import sys
import shutil
import time
from unittest.mock import patch, MagicMock

# 添加 src 到路径
sys.path.append(os.path.abspath("src"))

from x1ayu_rag_v2.api.ingest_api import IngestAPI
from x1ayu_rag_v2.config.constants import DEFAULT_CONFIG_DIR

def test_recursive_sync():
    # 1. Setup environment
    if os.path.exists(DEFAULT_CONFIG_DIR):
        shutil.rmtree(DEFAULT_CONFIG_DIR)
        
    test_dir = os.path.abspath("test_docs")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Create structure:
    # test_docs/
    #   doc1.md
    #   sub/
    #     doc2.md
    
    os.makedirs(os.path.join(test_dir, "sub"))
    with open(os.path.join(test_dir, "doc1.md"), "w") as f: f.write("# Doc 1")
    with open(os.path.join(test_dir, "sub", "doc2.md"), "w") as f: f.write("# Doc 2")
        
    try:
        # Mock ChunkRepository
        with patch("x1ayu_rag_v2.repository.document_repository.ChunkRepository") as MockChunkRepo:
            mock_chunk_repo_instance = MockChunkRepo.return_value
            mock_chunk_repo_instance.store_chunks.return_value = None
            mock_chunk_repo_instance.delete_by_document_id.return_value = None
            
            api = IngestAPI()
            
            # 2. Test Initial Sync (Recursive Add)
            print(f"\n--- 1. Initial Sync of {test_dir} ---")
            success, msg = api.ingest_document(test_dir)
            print(f"Result: {success}, {msg}")
            assert success
            assert "Added 2" in msg
            
            # Verify DB content
            repo = api.service.doc_repo
            all_docs = repo.list_all()
            print(f"Total docs in DB: {len(all_docs)}")
            assert len(all_docs) == 2
            
            # 3. Test No Change
            print(f"\n--- 2. Sync No Change ---")
            success, msg = api.ingest_document(test_dir)
            print(f"Result: {success}, {msg}")
            assert success
            assert "No changes detected" in msg
            
            # 4. Test Update and Delete
            print(f"\n--- 3. Sync Update and Delete ---")
            # Update doc1
            with open(os.path.join(test_dir, "doc1.md"), "w") as f: f.write("# Doc 1 Updated")
            # Delete doc2
            os.remove(os.path.join(test_dir, "sub", "doc2.md"))
            # Add doc3
            with open(os.path.join(test_dir, "doc3.md"), "w") as f: f.write("# Doc 3")
            
            success, msg = api.ingest_document(test_dir)
            print(f"Result: {success}, {msg}")
            assert success
            assert "Added 1" in msg
            assert "Updated 1" in msg
            assert "Deleted 1" in msg
            
            # Verify DB content
            all_docs = repo.list_all()
            print(f"Total docs in DB: {len(all_docs)}")
            assert len(all_docs) == 2 # doc1, doc3 (doc2 deleted)
            
            doc_names = [d.name for d in all_docs]
            assert "doc1.md" in doc_names
            assert "doc3.md" in doc_names
            assert "doc2.md" not in doc_names
            
            print("\nRecursive Sync Test Passed!")
            
    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        if os.path.exists(DEFAULT_CONFIG_DIR):
            shutil.rmtree(DEFAULT_CONFIG_DIR)

if __name__ == "__main__":
    try:
        test_recursive_sync()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
