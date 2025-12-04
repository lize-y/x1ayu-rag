import sqlite3

# 1. 连接到SQLite数据库（如果不存在，会自动创建）
conn = sqlite3.connect("demo.db")  # 文件名为 demo.db
cursor = conn.cursor()

# 2. 创建一个表
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER
)
"""
)
print("Table created successfully.")

# 3. 插入数据
cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Alice", 25))
cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Bob", 30))

# 批量插入
users = [("Charlie", 22), ("David", 28)]
cursor.executemany("INSERT INTO users (name, age) VALUES (?, ?)", users)

# 提交事务
conn.commit()
print("Data inserted successfully.")

# 4. 查询数据
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
print("All users:")
for row in rows:
    print(row)

# 查询特定条件
cursor.execute("SELECT * FROM users WHERE age > ?", (25,))
rows = cursor.fetchall()
print("Users older than 25:")
for row in rows:
    print(row)

# 5. 更新数据
cursor.execute("UPDATE users SET age = ? WHERE name = ?", (26, "Alice"))
conn.commit()
print("Data updated successfully.")

# 6. 删除数据
cursor.execute("DELETE FROM users WHERE name = ?", ("David",))
conn.commit()
print("Data deleted successfully.")

# 7. 查询更新后的数据
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
print("Updated users:")
for row in rows:
    print(row)

# 8. 关闭连接
cursor.close()
conn.close()
