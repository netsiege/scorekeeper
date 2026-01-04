"""
Task Queue Manager for dynamic endpoint management.
Manages task distribution to boxes and handles claim submissions.
"""
import threading
import yaml
import json
from typing import Optional


def _task_to_key(task: dict) -> str:
    """Convert a task dict to a hashable string key."""
    return json.dumps(task, sort_keys=True)


def _key_to_task(key: str) -> dict:
    """Convert a hashable string key back to a task dict."""
    return json.loads(key)


class TaskQueue:
    """
    Manages a queue of tasks for each box.
    Tasks are assigned to boxes and removed once a claim is submitted.
    Uses sets to prevent duplicate tasks.
    """
    
    def __init__(self):
        self._queues: dict[str, set[str]] = {}  # hostname -> set of task keys
        self._box_tasks: dict[str, dict[str, list[dict]]] = {}  # hostname -> configured tasks from phase yaml
        self._ip_to_hostname: dict[str, str] = {}  # IP address -> hostname mapping
        self._box_keys: dict[str, str] = {}  # hostname -> authentication key
        self._lock = threading.Lock()
    
    def load_phase_config(self, filepath: str) -> None:
        """Load box-specific tasks from a phase YAML configuration file."""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                boxes = data.get("boxes", [])
                
                for box in boxes:
                    hostname = box.get("name")
                    ip = box.get("ip")
                    if not hostname:
                        continue
                    
                    # Build IP to hostname mapping
                    if ip:
                        self._ip_to_hostname[ip] = hostname
                    
                    owner_tasks = []
                    non_owner_tasks = []
                    checks = box.get("checks", [])
                    
                    for check in checks:
                        # Generate check_control tasks from claim checks
                        if "claim" in check:
                            claim = check["claim"]
                            is_owner = claim.get("owner", False)
                            task = {
                                "type": "check_control",
                                "file_path": claim.get("path"),
                                "name": claim.get("name", "unknown"),
                                "value": claim.get("value", 1),
                                "owner": is_owner
                            }
                            if is_owner:
                                owner_tasks.append(task)
                            else:
                                non_owner_tasks.append(task)
                    
                    self._box_tasks[hostname] = {
                        "owner": owner_tasks,
                        "non_owner": non_owner_tasks,
                        "rotate_key": [{"type": "rotate_key"}]
                    }
                    
        except Exception as e:
            print(f"Error loading phase config: {e}")
    
    def get_hostname_by_ip(self, ip: str) -> Optional[str]:
        """Map a client IP address to a hostname based on the phase config."""
        with self._lock:
            return self._ip_to_hostname.get(ip)
    
    def set_box_key(self, hostname: str, key: str) -> None:
        """Set the authentication key for a specific box."""
        with self._lock:
            self._box_keys[hostname] = key
    
    def get_box_key(self, hostname: str) -> Optional[str]:
        """Get the authentication key for a specific box."""
        with self._lock:
            return self._box_keys.get(hostname)
    
    def verify_box_key(self, hostname: str, key: str) -> bool:
        """Verify if the provided key matches the stored key for a box."""
        with self._lock:
            stored_key = self._box_keys.get(hostname)
            if stored_key is None:
                return False
            return stored_key == key
    
    def get_box_task_config(self, hostname: str) -> dict[str, list[dict]]:
        """Get the configured tasks for a specific box from phase config."""
        return self._box_tasks.get(hostname, {"owner": [], "non_owner": [], "rotate_key": []})
    
    def get_owner_tasks(self, hostname: str) -> list[dict]:
        """Get owner claim tasks for a specific box."""
        config = self._box_tasks.get(hostname, {})
        return config.get("owner", [])
    
    def get_non_owner_tasks(self, hostname: str) -> list[dict]:
        """Get non-owner claim tasks for a specific box."""
        config = self._box_tasks.get(hostname, {})
        return config.get("non_owner", [])
    
    def get_rotate_key_tasks(self, hostname: str) -> list[dict]:
        """Get rotate_key tasks for a specific box."""
        config = self._box_tasks.get(hostname, {})
        return config.get("rotate_key", [])
    
    def add_task(self, hostname: str, task: dict) -> None:
        """Add a task to a box's queue (duplicates are ignored)."""
        with self._lock:
            if hostname not in self._queues:
                self._queues[hostname] = set()
            self._queues[hostname].add(_task_to_key(task))
    
    def add_tasks(self, hostname: str, tasks: list[dict]) -> None:
        """Add multiple tasks to a box's queue (duplicates are ignored)."""
        with self._lock:
            if hostname not in self._queues:
                self._queues[hostname] = set()
            for task in tasks:
                self._queues[hostname].add(_task_to_key(task))
    
    def populate_from_config(self, hostname: str, task_type: str = "all") -> None:
        """
        Populate a box's queue with tasks from its phase configuration.
        
        Args:
            hostname: The box hostname
            task_type: 'owner', 'non_owner', 'rotate_key', or 'all'
        """
        config = self.get_box_task_config(hostname)
        
        if task_type == "all":
            types_to_add = ["owner", "non_owner", "rotate_key"]
        else:
            types_to_add = [task_type]
        
        for t in types_to_add:
            for task in config.get(t, []):
                self.add_task(hostname, task.copy())
    
    def populate_all_from_config(self) -> None:
        """Populate all boxes' queues with tasks from their phase configuration."""
        for hostname in self._box_tasks:
            self.populate_from_config(hostname)
    
    def get_tasks(self, hostname: str) -> list[dict]:
        """Get all tasks for a specific box."""
        with self._lock:
            keys = self._queues.get(hostname, set())
            return [_key_to_task(k) for k in keys]
    
    def get_next_task(self, hostname: str) -> Optional[dict]:
        """Get a task for a box without removing it."""
        with self._lock:
            keys = self._queues.get(hostname, set())
            if keys:
                return _key_to_task(next(iter(keys)))
            return None
    
    def remove_task(self, hostname: str, task_index: int = 0) -> Optional[dict]:
        """Remove a task from a box's queue."""
        with self._lock:
            if hostname in self._queues and self._queues[hostname]:
                key = next(iter(self._queues[hostname]))
                self._queues[hostname].discard(key)
                return _key_to_task(key)
        return None
    
    def task_type_exists(self, hostname: str, task_type: str) -> bool:
        """Check if a task of a specific type exists in a box's queue."""
        with self._lock:
            if hostname in self._queues:
                for key in list(self._queues[hostname]):
                    task = _key_to_task(key)
                    if task.get("type") == task_type:
                        return True
        return False
    
    def remove_task_by_type(self, hostname: str, task_type: str) -> Optional[dict]:
        """Remove the first task of a specific type from a box's queue."""
        with self._lock:
            if hostname in self._queues:
                for key in list(self._queues[hostname]):
                    task = _key_to_task(key)
                    if task.get("type") == task_type:
                        self._queues[hostname].discard(key)
                        return task
        return None
    
    def remove_task_by_path(self, hostname: str, file_path: str) -> Optional[dict]:
        """Remove a task with a specific file_path from a box's queue."""
        with self._lock:
            if hostname in self._queues:
                for key in list(self._queues[hostname]):
                    task = _key_to_task(key)
                    if task.get("file_path") == file_path:
                        self._queues[hostname].discard(key)
                        return task
        return None
    
    def clear_tasks(self, hostname: str) -> None:
        """Clear all tasks for a specific box."""
        with self._lock:
            if hostname in self._queues:
                self._queues[hostname] = set()
    
    def clear_all(self) -> None:
        """Clear all task queues."""
        with self._lock:
            self._queues = {}
    
    def get_all_queues(self) -> dict[str, list[dict]]:
        """Get a copy of all task queues."""
        with self._lock:
            return {k: [_key_to_task(key) for key in v] for k, v in self._queues.items()}
    
    def has_tasks(self, hostname: str) -> bool:
        """Check if a box has any pending tasks."""
        with self._lock:
            return hostname in self._queues and len(self._queues[hostname]) > 0
    
    def task_count(self, hostname: str) -> int:
        """Get the number of pending tasks for a box."""
        with self._lock:
            return len(self._queues.get(hostname, set()))


# Global task queue instance
task_queue = TaskQueue()
