"""Workflow management for BGWpy task orchestration.

This module provides the Workflow class for managing sequences of tasks,
including parallel and sequential execution patterns.
"""

from __future__ import annotations

import shlex
from typing import TYPE_CHECKING, Any

from .task import Task, TaskStatus
from .util import relative_path

if TYPE_CHECKING:
    from collections.abc import Iterator


class Workflow(Task):
    """Sequence of computational tasks.

    A Workflow manages multiple tasks that can be executed sequentially
    or merged into a single execution script. Tasks are written from the
    workflow's main directory.

    Attributes
    ----------
    tasks : list[Task]
        List of tasks in this workflow.

    Examples
    --------
    Create a workflow with tasks in subdirectories:

    >>> workflow = Workflow(dirname='calculation')
    >>> scf_task = Task(dirname='calculation/scf')
    >>> bands_task = Task(dirname='calculation/bands')
    >>> workflow.add_task(scf_task)
    >>> workflow.add_task(bands_task)
    >>> workflow.write()

    Create a workflow with merged tasks (single directory):

    >>> workflow = Workflow(dirname='calculation')
    >>> task1 = Task(dirname='calculation')
    >>> task2 = Task(dirname='calculation')
    >>> workflow.add_task(task1, merge=True)
    >>> workflow.add_task(task2, merge=True)
    """

    def __init__(
        self,
        tasks: list[Task] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a workflow.

        Parameters
        ----------
        tasks : list[Task] | None, default=None
            Initial tasks to add to the workflow.
        *args
            Positional arguments passed to Task.__init__.
        **kwargs
            Keyword arguments passed to Task.__init__.
        """
        super().__init__(*args, **kwargs)
        self.tasks: list[Task] = []
        if tasks is not None:
            self.tasks.extend(tasks)

    def add_task(self, task: Task, *, merge: bool = False) -> None:
        """Add a task to the workflow.

        Parameters
        ----------
        task : Task
            The task to add.
        merge : bool, default=False
            If True, merge the task's runscript into the workflow's runscript.
            Only works if task has the same dirname as the workflow.

        Raises
        ------
        ValueError
            If merge=True but directories don't match.
            If a task with the same directory and runscript name already exists.

        Notes
        -----
        When merge=False, the workflow's runscript will cd into the task's
        directory, execute the task's runscript, and cd back.

        When merge=True, the task's commands are merged directly into the
        workflow's runscript, allowing all tasks to execute in sequence
        without directory changes.

        Examples
        --------
        Add tasks in separate directories:

        >>> workflow.add_task(scf_task)
        >>> workflow.add_task(bands_task)

        Merge tasks in the same directory:

        >>> workflow.add_task(task1, merge=True)
        >>> workflow.add_task(task2, merge=True)
        """
        if merge:
            if self.dirname != task.dirname:
                msg = (
                    f"Cannot merge task with different dirname. "
                    f"Workflow: {self.dirname}, Task: {task.dirname}"
                )
                raise ValueError(msg)
            self.runscript.merge(task.runscript)

        else:
            # Check for duplicate task (same directory and runscript name)
            self._check_duplicate_task(task)

            # Add commands to change to task directory and run it
            if task.dirname != self.dirname:
                self._add_task_execution_commands(task)
            else:
                # Same directory, just run the script
                self.runscript.append(f"bash {task.runscript.fname}")

        self.tasks.append(task)

    def _check_duplicate_task(self, task: Task) -> None:
        """Check if a task with same directory and runscript already exists.

        Parameters
        ----------
        task : Task
            Task to check.

        Raises
        ------
        ValueError
            If a duplicate task is found.
        """
        for existing_task in self.tasks:
            if (
                existing_task.dirname == task.dirname
                and existing_task.runscript.fname == task.runscript.fname
            ):
                msg = (
                    f"Duplicate task detected:\n"
                    f"  Directory: {task.dirname}\n"
                    f"  Runscript: {task.runscript.fname}\n"
                    f"Use a different runscript_fname to distinguish tasks."
                )
                raise ValueError(msg)

    def _add_task_execution_commands(self, task: Task) -> None:
        """Add commands to execute a task in a different directory.

        Parameters
        ----------
        task : Task
            Task to execute.

        Notes
        -----
        Adds commands to:
        1. cd into the task's directory
        2. Execute the task's runscript
        3. cd back to the workflow directory
        """
        # Use pathlib for cleaner relative path calculation
        rel_task_dir = relative_path(task.dirname, self.dirname)
        rel_back_dir = relative_path(self.dirname, task.dirname)

        self.runscript.append(f"cd {shlex.quote(rel_task_dir)}")
        self.runscript.append(f"bash {task.runscript.fname}")
        self.runscript.append(f"cd {shlex.quote(rel_back_dir)}")

    def add_tasks(
        self,
        tasks: list[Task],
        *,
        merge: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add multiple tasks to the workflow.

        Parameters
        ----------
        tasks : list[Task]
            Tasks to add.
        merge : bool, default=False
            Whether to merge all tasks.
        **kwargs
            Additional keyword arguments passed to add_task.

        Examples
        --------
        >>> workflow.add_tasks([task1, task2, task3])
        >>> workflow.add_tasks([task1, task2], merge=True)
        """
        for task in tasks:
            self.add_task(task, merge=merge, **kwargs)

    def write(self) -> None:
        """Write the workflow and all its tasks to disk.

        This method:
        1. Writes the workflow's directory and runscript
        2. Writes all child tasks
        3. Overwrites the workflow's runscript (to include task execution)

        Notes
        -----
        Child task runscripts are written first, then the workflow runscript
        is written last to ensure it contains the correct task execution order.
        """
        super().write()

        # Write all child tasks
        for task in self.tasks:
            task.write()

        # Overwrite workflow runscript with final version
        with self.exec_from_dirname():
            self.runscript.write()

    def get_status(self, **kwargs: Any) -> TaskStatus:
        """Get the workflow status based on task statuses.

        The workflow is considered complete only if all tasks are complete.
        Otherwise, returns the status of the first incomplete task.

        Parameters
        ----------
        **kwargs
            Additional arguments passed to task.get_status().

        Returns
        -------
        TaskStatus
            COMPLETED if all tasks are complete, otherwise the status
            of the first incomplete task.

        Examples
        --------
        >>> workflow.get_status()
        TaskStatus.COMPLETED
        >>> workflow.get_status(check_time=True)
        TaskStatus.UNSTARTED
        """
        for task in self.tasks:
            status = task.get_status(**kwargs)
            if status != TaskStatus.COMPLETED:
                return status

        return TaskStatus.COMPLETED

    def is_complete(self) -> bool:
        """Check if all tasks in the workflow are complete.

        Returns
        -------
        bool
            True if all tasks report COMPLETED status.

        Examples
        --------
        >>> workflow.is_complete()
        True
        """
        return all(task.is_complete() for task in self.tasks)

    def report(self, *args: Any, **kwargs: Any) -> None:
        """Report the status of all tasks in the workflow.

        Parameters
        ----------
        *args
            Positional arguments passed to task.report().
        **kwargs
            Keyword arguments passed to task.report().

        Examples
        --------
        >>> workflow.report()
           SCF        : ./calculation/scf    -  Status :  Completed
           Bands      : ./calculation/bands  -  Status :  Unstarted
        """
        for task in self.tasks:
            task.report(*args, **kwargs)

    def __iter__(self) -> Iterator[Task]:
        """Iterate over all tasks, recursively flattening nested workflows.

        Yields
        ------
        Task
            Each task in the workflow. If a task is itself a workflow,
            yields its sub-tasks recursively.

        Examples
        --------
        >>> for task in workflow:
        ...     print(task.dirname)
        ./calculation/scf
        ./calculation/bands
        ./calculation/epsilon

        Notes
        -----
        This allows workflows to contain other workflows, creating a
        hierarchical task structure that can be flattened for iteration.
        """
        for task in self.tasks:
            if isinstance(task, Workflow):
                # Recursively yield tasks from nested workflows
                yield from task
            else:
                yield task

    def __len__(self) -> int:
        """Return the number of direct child tasks.

        Returns
        -------
        int
            Number of tasks directly in this workflow.

        Notes
        -----
        This returns the number of direct children, not the total
        number of tasks including nested workflows. Use len(list(workflow))
        to get the total flattened task count.

        Examples
        --------
        >>> len(workflow)
        3
        """
        return len(self.tasks)

    def __repr__(self) -> str:
        """Return a string representation of the workflow.

        Returns
        -------
        str
            String representation showing dirname and task count.

        Examples
        --------
        >>> workflow
        Workflow(dirname='calculation', tasks=3)
        """
        return f"Workflow(dirname={self.dirname!r}, tasks={len(self.tasks)})"
