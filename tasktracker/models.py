from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any

from .utils import to_iso, from_iso


class TaskStatus(str, Enum):
    """
    Enumeration of valid task status values.
    
    Values:
        OPEN: Task is newly created and not yet started
        IN_PROGRESS: Task is currently being worked on
        DONE: Task has been completed
    """
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(IntEnum):
    """
    Enumeration of valid task priority levels.
    
    Priority ranges from 1 (highest) to 5 (lowest).
    Lower numbers indicate higher priority.
    
    Values:
        ONE: Highest priority (1)
        TWO: High priority (2)
        THREE: Medium priority (3)
        FOUR: Low priority (4)
        FIVE: Lowest priority (5)
    """
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

@dataclass
class Task:
    """
    Represents a task in the task tracker system.
    
    Attributes:
        id: Unique identifier (UUID string) for the task
        title: Task title (required, non-empty after strip)
        description: Task description (can be empty)
        status: Task status (TaskStatus enum: OPEN, IN_PROGRESS, or DONE)
        priority: Task priority (TaskPriority enum: 1-5, where 1 is highest)
        created_at: Timestamp when task was created (timezone-aware UTC)
        updated_at: Timestamp when task was last updated (timezone-aware UTC)
    """
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """
        Post-initialization hook to convert string/int values to enums.
        
        This allows backward compatibility where Task can be created with
        string status values ("OPEN", "IN_PROGRESS", "DONE") and integer
        priority values (1-5), which are automatically converted to enums.
        """
        # Convert string status to TaskStatus enum if needed
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        elif not isinstance(self.status, TaskStatus):
            raise ValueError(f"Invalid status type: {type(self.status)}. Expected TaskStatus or str.")
        
        # Convert integer priority to TaskPriority enum if needed
        if isinstance(self.priority, int):
            self.priority = TaskPriority(self.priority)
        elif not isinstance(self.priority, TaskPriority):
            raise ValueError(f"Invalid priority type: {type(self.priority)}. Expected TaskPriority or int.")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert Task instance to a JSON-serializable dictionary.
        
        Converts datetime objects to ISO format strings with timezone offset.
        Converts enum objects to their underlying values (string for status, int for priority).
        This ensures the dict can be serialized to JSON and properly reconstructed.
        
        Returns:
            Dictionary containing all task fields with timestamps as ISO strings
            and enums as their underlying values.
            Example: {
                "id": "...",
                "title": "...",
                "description": "...",
                "status": "OPEN",
                "priority": 2,
                "created_at": "2026-02-10T10:00:00+00:00",
                "updated_at": "2026-02-10T10:00:00+00:00"
            }
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            # Convert enum to its underlying value (string for Status, int for Priority)
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """
        Create a Task instance from a dictionary (typically from to_dict()).
        
        Parses ISO format timestamp strings back into timezone-aware datetime objects.
        Converts string/int values back to enum objects (TaskStatus and TaskPriority).
        This is the inverse operation of to_dict(), allowing round-trip serialization.
        
        Args:
            data: Dictionary containing task fields. Timestamps should be ISO strings
                  with timezone offset (e.g., "2026-02-10T10:00:00+00:00").
                  Status should be a string ("OPEN", "IN_PROGRESS", "DONE").
                  Priority should be an integer (1-5).
        
        Returns:
            Task instance with all fields populated from the dictionary.
        
        Raises:
            ValueError: If datetime strings don't include timezone offset,
                       or if status/priority values are invalid.
        """
        # Create a copy of the dict to avoid mutating the input
        task_data = data.copy()
        
        # Convert ISO string timestamps back to datetime objects
        task_data["created_at"] = from_iso(task_data["created_at"])
        task_data["updated_at"] = from_iso(task_data["updated_at"])
        
        # Convert string status value back to TaskStatus enum
        # Handle both enum instances and string values
        status_value = task_data["status"]
        if isinstance(status_value, TaskStatus):
            task_data["status"] = status_value
        else:
            task_data["status"] = TaskStatus(status_value)
        
        # Convert integer priority value back to TaskPriority enum
        # Handle both enum instances and integer values
        priority_value = task_data["priority"]
        if isinstance(priority_value, TaskPriority):
            task_data["priority"] = priority_value
        else:
            task_data["priority"] = TaskPriority(priority_value)
        
        # Create and return Task instance with unpacked dictionary
        return cls(**task_data)
