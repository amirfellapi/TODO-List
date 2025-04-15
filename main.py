from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiosqlite

app = FastAPI()

# Define the Task model
class Task(BaseModel):
    task: str
    completed: bool

# Connect to SQLite database
async def get_db():
    try:
        async with aiosqlite.connect("tasks.db") as db:
            return db
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to database: {str(e)}")

# Create table if not exists
@app.on_event("startup")
async def startup_event():
    try:
        async with aiosqlite.connect("tasks.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0
                )
            """)
            await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")

# Get all tasks
@app.get("/tasks")
async def get_tasks():
    try:
        async with aiosqlite.connect("tasks.db") as db:
            cursor = await db.execute("SELECT * FROM tasks")
            tasks = await cursor.fetchall()
            return [{"id": task[0], "task": task[1], "completed": bool(task[2])} for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")

# Add a new task
@app.post("/tasks")
async def add_task(task: Task):
    try:
        async with aiosqlite.connect("tasks.db") as db:
            await db.execute("INSERT INTO tasks (task, completed) VALUES (?, ?)", (task.task, int(task.completed)))
            await db.commit()
            return {"message": "Task added successfully"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to add task: {str(e)}")

# Update a task
@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    try:
        async with aiosqlite.connect("tasks.db") as db:
            cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            existing_task = await cursor.fetchone()
            if existing_task is None:
                raise HTTPException(status_code=404, detail="Task not found")
            await db.execute("UPDATE tasks SET task = ?, completed = ? WHERE id = ?", (task.task, int(task.completed), task_id))
            await db.commit()
            return {"message": "Task updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to update task: {str(e)}")

# Delete a task
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    try:
        async with aiosqlite.connect("tasks.db") as db:
            cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            existing_task = await cursor.fetchone()
            if existing_task is None:
                raise HTTPException(status_code=404, detail="Task not found")
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()
            return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to delete task: {str(e)}")
