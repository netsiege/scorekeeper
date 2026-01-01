"""
Task Queue Manager for dynamic endpoint management.
Manages task distribution to boxes and handles claim submissions.
"""
import threading
import json
from typing import Optional

# All possible task types loaded from tasks.json
TASK_TYPES = [
    {"type": "check_control", "file_path": "/tmp/ctrl.txt"},
    {"type": "rotate_key"},
    {"type": "check_control", "file_path": "/home/inspire/ctrl.txt"}
]


class TaskQueue:
    """
    Manages a queue of tasks for each box.
    Tasks are assigned to boxes and removed once a claim is submitted.
    """
    
    def __init__(self):
        self._queues: dict[str, list[dict]] = {}  # hostname -> list of tasks
        self._lock = threading.Lock()
    
    def load_task_types(self, filepath: str = "tasks.json") -> None:
        """Load available task types from a JSON file."""
        global TASK_TYPES
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                TASK_TYPES = data.get("tasks", [])
        except Exception as e:
            print(f"Error loading task types: {e}")
    
    def add_task(self, hostname: str, task: dict) -> None:
        """Add a task to a box's queue."""
        with self._lock:
            if hostname not in self._queues:
                self._queues[hostname] = []
            self._queues[hostname].append(task)
    
    def add_tasks(self, hostname: str, tasks: list[dict]) -> None:
        """Add multiple tasks to a box's queue."""
        with self._lock:
            if hostname not in self._queues:
                self._queues[hostname] = []
            self._queues[hostname].extend(tasks)
    
    def get_tasks(self, hostname: str) -> list[dict]:
        """Get all tasks for a specific box."""
        with self._lock:
            return self._queues.get(hostname, []).copy()
    
    def get_next_task(self, hostname: str) -> Optional[dict]:
        """Get the next task for a box without removing it."""
        with self._lock:
            tasks = self._queues.get(hostname, [])
            return tasks[0] if tasks else None
    
    def remove_task(self, hostname: str, task_index: int = 0) -> Optional[dict]:
        """Remove a task from a box's queue by index."""
        with self._lock:
            if hostname in self._queues and self._queues[hostname]:
                if 0 <= task_index < len(self._queues[hostname]):
                    return self._queues[hostname].pop(task_index)
        return None
    
    def remove_task_by_type(self, hostname: str, task_type: str) -> Optional[dict]:
        """Remove the first task of a specific type from a box's queue."""
        with self._lock:
            if hostname in self._queues:
                for i, task in enumerate(self._queues[hostname]):
                    if task.get("type") == task_type:
                        return self._queues[hostname].pop(i)
        return None
    
    def clear_tasks(self, hostname: str) -> None:
        """Clear all tasks for a specific box."""
        with self._lock:
            if hostname in self._queues:
                self._queues[hostname] = []
    
    def clear_all(self) -> None:
        """Clear all task queues."""
        with self._lock:
            self._queues = {}
    
    def get_all_queues(self) -> dict[str, list[dict]]:
        """Get a copy of all task queues."""
        with self._lock:
            return {k: v.copy() for k, v in self._queues.items()}
    
    def has_tasks(self, hostname: str) -> bool:
        """Check if a box has any pending tasks."""
        with self._lock:
            return hostname in self._queues and len(self._queues[hostname]) > 0
    
    def task_count(self, hostname: str) -> int:
        """Get the number of pending tasks for a box."""
        with self._lock:
            return len(self._queues.get(hostname, []))


# Global task queue instance
task_queue = TaskQueue()
