"""
Task Scheduler for automatically queuing tasks at random intervals.
Each task type (owner, non_owner, rotate_key) runs on its own schedule.
Owner claims are queued together, non-owner claims are queued together.
"""
import threading
import time
import random
from typing import Callable

DEBUG = 1


class TaskScheduler:
    """
    Schedules task queuing at random intervals with jitter.
    Queues all tasks of a type together when the interval fires.
    """
    
    def __init__(self):
        self._threads: list[threading.Thread] = []
        self._running = False
    
    def start_scheduler(
        self,
        task_type: str,
        interval: int,
        jitter: int,
        queue_func: Callable[[str, str], None],
        hostnames: list[str]
    ) -> None:
        """
        Start a background thread to queue tasks at random intervals.
        
        Args:
            task_type: 'owner', 'non_owner', or 'rotate_key'
            interval: Base interval in seconds between task queuing
            jitter: Random jitter in seconds to add to interval
            queue_func: Function to call to queue tasks (takes hostname and task_type)
            hostnames: List of box hostnames to queue tasks for
        """
        def scheduler_loop():
            while self._running:
                sleep_time = interval + random.randrange(max(1, jitter))
                if DEBUG:
                    print(f"[TaskScheduler] {task_type}: sleeping for {sleep_time}s")
                time.sleep(sleep_time)
                
                if not self._running:
                    break
                    
                for hostname in hostnames:
                    queue_func(hostname, task_type)
                    if DEBUG:
                        print(f"[TaskScheduler] Queued all {task_type} tasks for {hostname}")
        
        thread = threading.Thread(target=scheduler_loop, daemon=True, name=f"scheduler_{task_type}")
        self._threads.append(thread)
        thread.start()
        if DEBUG:
            print(f"[TaskScheduler] Started scheduler for {task_type} (interval={interval}s, jitter={jitter}s)")
    
    def start_all(
        self,
        task_config: dict,
        queue_func: Callable[[str, str], None],
        hostnames: list[str]
    ) -> None:
        """
        Start schedulers for all task types based on config.
        
        Args:
            task_config: Dict with 'owner', 'non_owner', 'rotate_key' keys,
                         each containing 'interval' and 'jitter'
            queue_func: Function to call to queue all tasks of a type
            hostnames: List of box hostnames
        """
        self._running = True
        
        for task_type in ['owner', 'non_owner', 'rotate_key']:
            config = task_config.get(task_type, {})
            interval = config.get('interval', 300)
            jitter = config.get('jitter', 60)
            
            self.start_scheduler(task_type, interval, jitter, queue_func, hostnames)
    
    def stop_all(self) -> None:
        """Stop all scheduler threads."""
        self._running = False
        if DEBUG:
            print("[TaskScheduler] Stopping all schedulers")


# Global scheduler instance
task_scheduler = TaskScheduler()
