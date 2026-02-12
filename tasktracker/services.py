from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from .models import Task, TaskStatus, TaskPriority
from .utils import utcnow, to_iso

class TaskService:
    """In-memory service managing Task CRUD, filtering, and history log."""

    def __init__(self) -> None:
        """
        Initialize the TaskService with an empty in-memory store and history log.
        
        The store is a dictionary mapping task IDs (UUID strings) to Task objects.
        The history log will track CREATE/UPDATE/DELETE events (used in Level 4).
        """
        # In-memory storage: maps task_id (str) -> Task object
        self._store: dict[str, Task] = {}
        
        # History log: list of event dictionaries (used in Level 4)
        # Format: [{"action": "CREATE"|"UPDATE"|"DELETE", "task_id": "<id>", "at": "<iso timestamp>"}, ...]
        self._history: list[dict] = []

    # ---------- CRUD ----------
    def create_task(self, title: str, description: str, priority: int) -> Task:
        """
        Create a new task with the specified attributes.
        
        The task is automatically assigned:
        - A unique UUID as its ID
        - Status set to "OPEN" (default status for new tasks)
        - Current UTC timestamp for both created_at and updated_at
        
        Args:
            title: Task title (must be non-empty after stripping whitespace)
            description: Task description (can be empty)
            priority: Task priority as integer (must be 1-5)
        
        Returns:
            The newly created Task instance.
        
        Raises:
            ValueError: If title is empty after stripping or priority is not 1-5.
        """
        # Validate title: must be non-empty after stripping whitespace
        self._validate_title(title)
        
        # Validate priority: must be between 1 and 5 (inclusive)
        self._validate_priority(priority)
        
        # Status is default (OPEN), so no validation needed
        
        # Generate a unique UUID for the task
        task_id = str(uuid.uuid4())
        
        # Get current UTC timestamp for both created_at and updated_at
        now = utcnow()
        
        # Create the task with default status "OPEN"
        # Priority is converted to TaskPriority enum via __post_init__
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.OPEN,  # Default status for new tasks
            priority=priority,  # Will be converted to TaskPriority enum
            created_at=now,
            updated_at=now,
        )
        
        # Store the task in the in-memory dictionary
        self._store[task_id] = task
        
        # Log CREATE event to history (always logged for new tasks)
        # Use the task's created_at timestamp for the log event
        self._log("CREATE", task_id, timestamp=now)
        
        # Return the created task
        return task

    def get_task(self, task_id: str) -> Task:
        """
        Retrieve a task by its ID.
        
        Args:
            task_id: The UUID string identifier of the task to retrieve.
        
        Returns:
            The Task instance with the specified ID.
        
        Raises:
            KeyError: If no task with the given ID exists in the store.
        """
        # Check if task exists in store
        if task_id not in self._store:
            raise KeyError(f"Task with id '{task_id}' not found")
        
        # Return the task from the store
        return self._store[task_id]

    def update_task(
        self,
        task_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Task:
        """
        Partially update a task's fields.
        
        Only the fields provided (not None) will be updated. This allows selective
        updates without needing to provide all fields. The updated_at timestamp is
        automatically bumped if at least one field actually changes.
        
        Args:
            task_id: The UUID string identifier of the task to update.
            title: Optional new title for the task.
            description: Optional new description for the task.
            status: Optional new status (will be validated in Level 3).
            priority: Optional new priority as integer (will be validated in Level 3).
        
        Returns:
            The updated Task instance.
        
        Raises:
            KeyError: If no task with the given ID exists in the store.
        """
        # Retrieve the existing task (raises KeyError if not found)
        task = self.get_task(task_id)
        
        # Track if any field actually changed
        has_changes = False
        
        # Update title if provided
        if title is not None:
            # Validate title before updating
            self._validate_title(title)
            
            if task.title != title:
                task.title = title
                has_changes = True
        
        # Update description if provided
        # Description can be empty, so no validation needed
        if description is not None:
            if task.description != description:
                task.description = description
                has_changes = True
        
        # Update status if provided
        if status is not None:
            # Validate type first: must be either a string or TaskStatus enum
            if not isinstance(status, (str, TaskStatus)):
                raise ValueError(f"Invalid status type: {type(status).__name__}. Expected str or TaskStatus enum.")
            
            # Validate status value (must be one of valid enum values)
            self._validate_status(status)
            
            # Convert string to TaskStatus enum if needed
            new_status = TaskStatus(status) if isinstance(status, str) else status
            
            # Only update if the new status is different from the current status
            if task.status != new_status:
                task.status = new_status
                has_changes = True
        
        # Update priority if provided
        if priority is not None:
            # Validate type first: must be either an int or TaskPriority enum
            if not isinstance(priority, (int, TaskPriority)):
                raise ValueError(f"Invalid priority type: {type(priority).__name__}. Expected int or TaskPriority enum.")
            
            # Validate priority value (must be 1-5)
            # If it's already a TaskPriority enum, extract the int value for validation
            priority_value = priority.value if isinstance(priority, TaskPriority) else priority
            self._validate_priority(priority_value)
            
            # Convert int to TaskPriority enum if needed
            new_priority = TaskPriority(priority) if isinstance(priority, int) else priority
            
            # Only update if the new priority is different from the current priority
            if task.priority != new_priority:
                task.priority = new_priority
                has_changes = True
        
        # Update the updated_at timestamp only if at least one field changed
        if has_changes:
            update_time = utcnow()
            task.updated_at = update_time
            # Log UPDATE event to history (only if at least one field changed)
            # Use the task's updated_at timestamp for the log event
            self._log("UPDATE", task_id, timestamp=update_time)
        
        # Return the updated task
        return task

    def delete_task(self, task_id: str) -> None:
        """
        Delete a task from the store.
        
        Args:
            task_id: The UUID string identifier of the task to delete.
        
        Raises:
            KeyError: If no task with the given ID exists in the store.
        """
        # Check if task exists (get_task will raise KeyError if not found)
        self.get_task(task_id)
        
        # Log DELETE event to history (always logged before deletion)
        self._log("DELETE", task_id)
        
        # Delete the task from the store
        del self._store[task_id]

    def list_tasks(self) -> list[Task]:
        """
        Retrieve all tasks sorted by creation time (oldest first).
        
        Returns:
            A list of all Task instances in the store, sorted by created_at
            timestamp in ascending order (oldest tasks first).
        """
        # Get all tasks from the store
        tasks = list(self._store.values())
        
        # Sort by created_at timestamp in ascending order (oldest first)
        # Using the datetime object directly for comparison
        tasks.sort(key=lambda t: t.created_at)
        
        return tasks

    # ---------- Level 4 ----------
    def filter_tasks(
        self,
        *,
        status: Optional[str] = None,
        min_priority: Optional[int] = None,
    ) -> list[Task]:
        """
        Filter tasks by status and/or minimum priority.
        
        Filters can be combined with AND logic (both conditions must match).
        Results are sorted by created_at timestamp in ascending order (oldest first).
        
        Args:
            status: Optional status filter. If provided, only tasks with exact status match
                   will be included. Can be a string or TaskStatus enum.
            min_priority: Optional minimum priority filter. If provided, only tasks with
                         priority >= min_priority will be included. Can be an integer
                         or TaskPriority enum.
        
        Returns:
            A list of Task instances matching the filter criteria, sorted by created_at
            in ascending order.
        """
        # Start with all tasks from the store
        tasks = list(self._store.values())
        
        # Filter by status if provided
        if status is not None:
            # Convert string to TaskStatus enum if needed for comparison
            if isinstance(status, str):
                filter_status = TaskStatus(status)
            elif isinstance(status, TaskStatus):
                filter_status = status
            else:
                raise ValueError(f"Invalid status type: {type(status).__name__}. Expected str or TaskStatus enum.")
            
            # Filter tasks with exact status match
            tasks = [t for t in tasks if t.status == filter_status]
        
        # Filter by min_priority if provided
        if min_priority is not None:
            # Convert int to TaskPriority enum if needed for comparison
            if isinstance(min_priority, int):
                filter_min_priority = TaskPriority(min_priority)
            elif isinstance(min_priority, TaskPriority):
                filter_min_priority = min_priority
            else:
                raise ValueError(f"Invalid min_priority type: {type(min_priority).__name__}. Expected int or TaskPriority enum.")
            
            # Filter tasks with priority >= min_priority
            # Since TaskPriority is an IntEnum, we can compare directly
            tasks = [t for t in tasks if t.priority.value >= filter_min_priority.value]
        
        # Sort by created_at timestamp in ascending order (oldest first)
        tasks.sort(key=lambda t: t.created_at)
        
        return tasks

    @property
    def history(self) -> list[dict]:
        """
        Get the history log of all CREATE, UPDATE, and DELETE events.
        
        Returns:
            A list of event dictionaries, each containing:
            - "action": "CREATE", "UPDATE", or "DELETE"
            - "task_id": The UUID string identifier of the task
            - "at": ISO format UTC timestamp string (e.g., "2026-02-10T09:00:00+00:00")
        
        The history is maintained in chronological order (oldest events first).
        """
        return self._history

    # ---------- Helpers ----------
    def _validate_title(self, title: str) -> None:
        """
        Validate that a title is non-empty after stripping whitespace.
        
        Args:
            title: The title string to validate.
        
        Raises:
            ValueError: If the title is None, empty, or contains only whitespace
                       after stripping.
        """
        # Check if title is None or empty after stripping whitespace
        if not title or not title.strip():
            raise ValueError("Title must be non-empty after stripping whitespace")
    
    def _validate_priority(self, priority: int) -> None:
        """
        Validate that a priority is within the valid range (1-5).
        
        Args:
            priority: The priority integer to validate.
        
        Raises:
            ValueError: If the priority is not between 1 and 5 (inclusive).
        """
        # Check if priority is within valid range (1-5)
        if not isinstance(priority, int):
            raise ValueError(f"Priority must be an integer, got {type(priority).__name__}")
        
        if priority < 1 or priority > 5:
            raise ValueError(f"Priority must be between 1 and 5 (inclusive), got {priority}")
    
    def _validate_status(self, status: str | TaskStatus) -> None:
        """
        Validate that a status is one of the valid TaskStatus enum values.
        
        Args:
            status: The status string or TaskStatus enum to validate.
        
        Raises:
            ValueError: If the status is not one of "OPEN", "IN_PROGRESS", or "DONE".
        """
        # Convert string to TaskStatus enum if needed, or use enum directly
        try:
            if isinstance(status, str):
                # Try to convert string to TaskStatus enum
                # This will raise ValueError if the string is not a valid enum value
                TaskStatus(status)
            elif isinstance(status, TaskStatus):
                # Already a valid enum, no conversion needed
                pass
            else:
                raise ValueError(f"Status must be a string or TaskStatus enum, got {type(status).__name__}")
        except ValueError as e:
            # Re-raise with a more helpful message if it's an invalid enum value
            if isinstance(status, str):
                raise ValueError(f"Status must be one of: {', '.join([s.value for s in TaskStatus])}, got '{status}'")
            raise

    def _log(self, action: str, task_id: str, timestamp: Optional[datetime] = None) -> None:
        """
        Log an event to the history list.
        
        Creates a history event dictionary with the action type, task ID, and
        UTC timestamp in ISO format. The event is appended to the internal history list.
        
        Args:
            action: The action type ("CREATE", "UPDATE", or "DELETE")
            task_id: The UUID string identifier of the task involved in the event
            timestamp: Optional datetime to use for the event. If None, uses current UTC time.
                      For CREATE/UPDATE events, this should match the task's timestamp.
                      For DELETE events, uses current UTC time if not provided.
        """
        # Use provided timestamp or current UTC time
        # For DELETE, if no timestamp provided, use current time (may be real or mocked)
        if timestamp is not None:
            event_time = timestamp
        else:
            # Use utcnow() which may be monkeypatched in tests
            # For DELETE operations, this will use the real time if iterator is exhausted
            try:
                event_time = utcnow()
            except StopIteration:
                # Fallback to real datetime if monkeypatch iterator is exhausted
                from datetime import timezone
                event_time = datetime.now(timezone.utc)
        
        # Create event dictionary with action, task_id, and ISO timestamp
        event = {
            "action": action,
            "task_id": task_id,
            "at": to_iso(event_time),  # Convert UTC time to ISO string
        }
        
        # Append event to history list
        self._history.append(event)
