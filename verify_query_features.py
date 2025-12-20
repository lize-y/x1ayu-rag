import sys
import os
import unittest
from rich.console import Console
from rich.table import Table

# 添加 src 到路径以便导入
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from x1ayu_rag_v2.api.query_api import QueryAPI
from x1ayu_rag_v2.api.ingest_api import IngestAPI
from x1ayu_rag_v2.db.sqlite_db import SqliteDB

class TestQueryFeatures(unittest.TestCase):
    def setUp(self):
        # 使用测试数据库
        self.test_db = "test_rag.db"
        os.environ["SQLITE_DB_PATH"] = self.test_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # 初始化数据
        self.ingest_api = IngestAPI()
        self.query_api = QueryAPI()
        
        # 创建一些测试文件
        os.makedirs("test_docs_query", exist_ok=True)
        with open("test_docs_query/doc_alpha.md", "w") as f:
            f.write("# Alpha Content")
        with open("test_docs_query/doc_beta.md", "w") as f:
            f.write("# Beta Content")
        with open("test_docs_query/doc_gamma.md", "w") as f:
            f.write("# Gamma Content")

        # 摄取数据
        self.ingest_api.ingest_document(os.path.abspath("test_docs_query"))

    def tearDown(self):
        # 清理
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        import shutil
        if os.path.exists("test_docs_query"):
            shutil.rmtree("test_docs_query")

    def test_show_table_data(self):
        print("\n--- Testing Show (Table Data) ---")
        data = self.query_api.get_document_table_data()
        self.assertEqual(len(data), 3)
        
        # 验证返回字段
        first_row = data[0]
        self.assertIn("Name", first_row)
        self.assertIn("Path", first_row)
        self.assertIn("UUID", first_row)
        
        # 模拟 CLI 展示效果
        console = Console()
        table = Table(title="Documents")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="magenta")
        table.add_column("UUID", style="green")
        
        for row in data:
            table.add_row(row["Name"], row["Path"], row["UUID"])
            
        print("Table Preview:")
        console.print(table)

    def test_search_select(self):
        print("\n--- Testing Search & Select ---")
        # 1. 搜索 "beta"
        results = self.query_api.search_for_select("beta")
        self.assertEqual(len(results), 1)
        self.assertIn("doc_beta.md", results[0])
        print(f"Search 'beta' result: {results}")

        # 2. 搜索 "test_docs" (路径匹配)
        results_path = self.query_api.search_for_select("test_docs")
        self.assertEqual(len(results_path), 3) # 所有文件都在此路径下
        print(f"Search 'test_docs' result count: {len(results_path)}")
        
        # 3. 空搜索 (列出所有)
        results_all = self.query_api.search_for_select("")
        self.assertEqual(len(results_all), 3)

if __name__ == "__main__":
    unittest.main()
