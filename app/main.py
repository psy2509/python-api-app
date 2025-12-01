from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Pydantic モデルの定義
# リクエストボディのスキーマを定義します
class TodoCreate(BaseModel):
    """TODOアイテム作成時のリクエストボディのスキーマ"""
    title: str
    done: bool = False

# レスポンスや内部データ構造のスキーマを定義します
class TodoItem(TodoCreate):
    """TODOアイテムの完全なスキーマ（IDを含む）"""
    id: int

# FastAPI アプリケーションのインスタンス
app = FastAPI(
    title="Simple Todo API",
    description="FastAPIを使って実装したシンプルなTODOと挨拶のAPI"
)

# インメモリデータベースの代わりとなるデータストアとIDカウンター
# 実際の本番環境ではデータベース（PostgreSQL, MongoDBなど）を使用します
todos: Dict[int, TodoItem] = {}
next_id = 1

# ----------------------------------------------------
# 1. ヘルスチェック API
# ----------------------------------------------------
@app.get("/health", summary="ヘルスチェック", response_model=Dict[str, str])
def health_check():
    """
    アプリケーションが正常に動作しているかを確認するためのエンドポイントです。
    """
    return {"status": "ok"}

# ----------------------------------------------------
# 2. 挨拶 API
# ----------------------------------------------------
@app.get("/greet", summary="挨拶", response_model=Dict[str, str])
def greet(name: Optional[str] = None):
    """
    名前を渡すと挨拶を返します。
    名前が指定されない場合は、匿名への挨拶を返します。
    """
    if name:
        message = f"Hello, {name}!"
    else:
        message = "Hello, anonymous!"
        
    return {"message": message}

# ----------------------------------------------------
# 3. TODO 作成 API
# ----------------------------------------------------
@app.post("/todos", summary="TODOアイテムを作成", response_model=TodoItem, status_code=201)
def create_todo(todo: TodoCreate):
    """
    新しいTODOアイテムを作成します。
    """
    global next_id
    
    # 新しいTODOアイテムを作成し、IDを割り当てる
    new_todo = TodoItem(id=next_id, title=todo.title, done=todo.done)
    
    # データストアに保存
    todos[next_todo.id] = new_todo
    
    # 次のIDをインクリメント
    next_id += 1
    
    return new_todo

# ----------------------------------------------------
# その他：全TODOリストを取得するAPI (利便性のために追加)
# ----------------------------------------------------
@app.get("/todos", summary="全TODOアイテムを取得", response_model=List[TodoItem])
def list_todos():
    """
    現在保存されている全てのTODOアイテムのリストを返します。
    """
    return list(todos.values())