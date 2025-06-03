# scheduler/scheduler_system.py
import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import croniter
import logging

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    ONCE = "once"
    CRON = "cron"
    INTERVAL = "interval"

class ScheduleStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScheduledTask:
    id: str
    name: str
    description: str
    schedule_type: ScheduleType
    schedule_expression: str  # cron expression, interval in seconds, or datetime for once
    agent_name: str
    task_payload: Dict[str, Any]
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_at: datetime = None
    next_run: datetime = None
    last_run: datetime = None
    run_count: int = 0
    max_runs: Optional[int] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TaskExecution:
    execution_id: str
    task_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    result: str
    error: str
    duration_seconds: float

class TaskScheduler:
    """Advanced task scheduler with cron support"""
    
    def __init__(self, db_path: str = "scheduler.db"):
        self.db_path = db_path
        self.running = False
        self.task_handlers: Dict[str, Callable] = {}
        self._init_database()
        self._check_interval = 10  # Check every 10 seconds
    
    def _init_database(self):
        """Initialize the scheduler database"""
        conn = sqlite3.connect(self.db_path)
        
        # Scheduled tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                schedule_type TEXT,
                schedule_expression TEXT,
                agent_name TEXT,
                task_payload TEXT,
                status TEXT,
                created_at TEXT,
                next_run TEXT,
                last_run TEXT,
                run_count INTEGER,
                max_runs INTEGER,
                timeout_seconds INTEGER,
                retry_count INTEGER,
                max_retries INTEGER,
                metadata TEXT
            )
        ''')
        
        # Task executions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS task_executions (
                execution_id TEXT PRIMARY KEY,
                task_id TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT,
                result TEXT,
                error TEXT,
                duration_seconds REAL,
                FOREIGN KEY (task_id) REFERENCES scheduled_tasks (id)
            )
        ''')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_next_run ON scheduled_tasks(next_run)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON scheduled_tasks(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_agent ON scheduled_tasks(agent_name)')
        
        conn.commit()
        conn.close()
    
    def register_task_handler(self, agent_name: str, handler: Callable):
        """Register a task handler for an agent"""
        self.task_handlers[agent_name] = handler
        logger.info(f"Registered task handler for agent: {agent_name}")
    
    async def schedule_task(self, task: ScheduledTask) -> str:
        """Schedule a new task"""
        # Calculate next run time
        task.next_run = self._calculate_next_run(task)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO scheduled_tasks VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id, task.name, task.description,
            task.schedule_type.value, task.schedule_expression,
            task.agent_name, json.dumps(task.task_payload),
            task.status.value, task.created_at.isoformat(),
            task.next_run.isoformat() if task.next_run else None,
            task.last_run.isoformat() if task.last_run else None,
            task.run_count, task.max_runs, task.timeout_seconds,
            task.retry_count, task.max_retries, json.dumps(task.metadata)
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Scheduled task: {task.id} - {task.name}")
        return task.id
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate the next run time for a task"""
        now = datetime.now()
        
        if task.schedule_type == ScheduleType.ONCE:
            # For one-time tasks, parse the datetime
            try:
                return datetime.fromisoformat(task.schedule_expression)
            except ValueError:
                logger.error(f"Invalid datetime format for task {task.id}: {task.schedule_expression}")
                return None
        
        elif task.schedule_type == ScheduleType.CRON:
            # Use croniter for cron expressions
            try:
                cron = croniter.croniter(task.schedule_expression, now)
                return cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron expression for task {task.id}: {e}")
                return None
        
        elif task.schedule_type == ScheduleType.INTERVAL:
            # For interval tasks, add seconds to current time
            try:
                interval_seconds = int(task.schedule_expression)
                base_time = task.last_run if task.last_run else now
                return base_time + timedelta(seconds=interval_seconds)
            except ValueError:
                logger.error(f"Invalid interval for task {task.id}: {task.schedule_expression}")
                return None
        
        return None
    
    async def get_scheduled_tasks(self, agent_name: str = None, 
                                status: ScheduleStatus = None) -> List[ScheduledTask]:
        """Get scheduled tasks with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM scheduled_tasks WHERE 1=1"
        params = []
        
        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY next_run ASC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task = ScheduledTask(
                id=row[0], name=row[1], description=row[2],
                schedule_type=ScheduleType(row[3]),
                schedule_expression=row[4], agent_name=row[5],
                task_payload=json.loads(row[6]),
                status=ScheduleStatus(row[7]),
                created_at=datetime.fromisoformat(row[8]),
                next_run=datetime.fromisoformat(row[9]) if row[9] else None,
                last_run=datetime.fromisoformat(row[10]) if row[10] else None,
                run_count=row[11], max_runs=row[12],
                timeout_seconds=row[13], retry_count=row[14],
                max_retries=row[15], metadata=json.loads(row[16])
            )
            tasks.append(task)
        
        return tasks
    
    async def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        return await self._update_task_status(task_id, ScheduleStatus.PAUSED)
    
    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        return await self._update_task_status(task_id, ScheduleStatus.ACTIVE)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        return await self._update_task_status(task_id, ScheduleStatus.CANCELLED)
    
    async def _update_task_status(self, task_id: str, status: ScheduleStatus) -> bool:
        """Update task status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'UPDATE scheduled_tasks SET status = ? WHERE id = ?',
            (status.value, task_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if affected > 0:
            logger.info(f"Updated task {task_id} status to {status.value}")
        
        return affected > 0
    
    async def start_scheduler(self):
        """Start the scheduler loop"""
        self.running = True
        logger.info("Task scheduler started")
        
        while self.running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    async def _check_and_run_tasks(self):
        """Check for tasks that need to run and execute them"""
        now = datetime.now()
        
        # Get tasks that are ready to run
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT * FROM scheduled_tasks 
            WHERE status = ? AND next_run <= ? 
            ORDER BY next_run ASC
        ''', (ScheduleStatus.ACTIVE.value, now.isoformat()))
        
        ready_tasks = cursor.fetchall()
        conn.close()
        
        for task_row in ready_tasks:
            task = self._row_to_task(task_row)
            
            # Check if max runs reached
            if task.max_runs and task.run_count >= task.max_runs:
                await self._update_task_status(task.id, ScheduleStatus.COMPLETED)
                continue
            
            # Execute task
            await self._execute_task(task)
    
    def _row_to_task(self, row) -> ScheduledTask:
        """Convert database row to ScheduledTask object"""
        return ScheduledTask(
            id=row[0], name=row[1], description=row[2],
            schedule_type=ScheduleType(row[3]),
            schedule_expression=row[4], agent_name=row[5],
            task_payload=json.loads(row[6]),
            status=ScheduleStatus(row[7]),
            created_at=datetime.fromisoformat(row[8]),
            next_run=datetime.fromisoformat(row[9]) if row[9] else None,
            last_run=datetime.fromisoformat(row[10]) if row[10] else None,
            run_count=row[11], max_runs=row[12],
            timeout_seconds=row[13], retry_count=row[14],
            max_retries=row[15], metadata=json.loads(row[16])
        )
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        execution_id = f"{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Executing scheduled task: {task.id} - {task.name}")
        
        # Record execution start
        await self._record_execution_start(execution_id, task.id, start_time)
        
        try:
            # Get task handler
            if task.agent_name not in self.task_handlers:
                raise Exception(f"No handler registered for agent: {task.agent_name}")
            
            handler = self.task_handlers[task.agent_name]
            
            # Execute task with timeout
            try:
                result = await asyncio.wait_for(
                    handler(task.task_payload),
                    timeout=task.timeout_seconds
                )
                
                # Record successful execution
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                await self._record_execution_complete(
                    execution_id, end_time, "completed", str(result), "", duration
                )
                
                # Update task for next run
                await self._update_task_after_execution(task, True)
                
                logger.info(f"Task {task.id} executed successfully")
                
            except asyncio.TimeoutError:
                # Handle timeout
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                await self._record_execution_complete(
                    execution_id, end_time, "timeout", "", "Task timed out", duration
                )
                
                await self._handle_task_failure(task, "Task timed out")
                
            except Exception as e:
                # Handle execution error
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                await self._record_execution_complete(
                    execution_id, end_time, "failed", "", str(e), duration
                )
                
                await self._handle_task_failure(task, str(e))
                
        except Exception as e:
            # Handle setup/handler errors
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            await self._record_execution_complete(
                execution_id, end_time, "error", "", str(e), duration
            )
            
            logger.error(f"Failed to execute task {task.id}: {e}")
    
    async def _record_execution_start(self, execution_id: str, task_id: str, start_time: datetime):
        """Record the start of task execution"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO task_executions 
            (execution_id, task_id, started_at, status) 
            VALUES (?, ?, ?, ?)
        ''', (execution_id, task_id, start_time.isoformat(), "running"))
        conn.commit()
        conn.close()
    
    async def _record_execution_complete(self, execution_id: str, end_time: datetime,
                                       status: str, result: str, error: str, duration: float):
        """Record the completion of task execution"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            UPDATE task_executions 
            SET completed_at = ?, status = ?, result = ?, error = ?, duration_seconds = ?
            WHERE execution_id = ?
        ''', (end_time.isoformat(), status, result, error, duration, execution_id))
        conn.commit()
        conn.close()
    
    async def _update_task_after_execution(self, task: ScheduledTask, success: bool):
        """Update task after execution"""
        # Update run count and last run time
        task.run_count += 1
        task.last_run = datetime.now()
        
        if success:
            task.retry_count = 0  # Reset retry count on success
        
        # Calculate next run time
        if task.schedule_type == ScheduleType.ONCE:
            # One-time task is completed
            task.status = ScheduleStatus.COMPLETED
            task.next_run = None
        else:
            # Calculate next run for recurring tasks
            task.next_run = self._calculate_next_run(task)
            
            # Check if max runs reached
            if task.max_runs and task.run_count >= task.max_runs:
                task.status = ScheduleStatus.COMPLETED
                task.next_run = None
        
        # Update in database
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            UPDATE scheduled_tasks 
            SET run_count = ?, last_run = ?, next_run = ?, status = ?, retry_count = ?
            WHERE id = ?
        ''', (
            task.run_count,
            task.last_run.isoformat(),
            task.next_run.isoformat() if task.next_run else None,
            task.status.value,
            task.retry_count,
            task.id
        ))
        conn.commit()
        conn.close()
    
    async def _handle_task_failure(self, task: ScheduledTask, error_message: str):
        """Handle task execution failure"""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Schedule retry
            retry_delay = min(60 * (2 ** task.retry_count), 3600)  # Exponential backoff, max 1 hour
            task.next_run = datetime.now() + timedelta(seconds=retry_delay)
            
            logger.info(f"Scheduling retry {task.retry_count}/{task.max_retries} for task {task.id} in {retry_delay} seconds")
        else:
            # Max retries reached, mark as failed
            task.status = ScheduleStatus.FAILED
            task.next_run = None
            
            logger.error(f"Task {task.id} failed after {task.max_retries} retries")
        
        # Update in database
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            UPDATE scheduled_tasks 
            SET retry_count = ?, next_run = ?, status = ?
            WHERE id = ?
        ''', (
            task.retry_count,
            task.next_run.isoformat() if task.next_run else None,
            task.status.value,
            task.id
        ))
        conn.commit()
        conn.close()
    
    async def get_task_executions(self, task_id: str = None, limit: int = 100) -> List[TaskExecution]:
        """Get task execution history"""
        conn = sqlite3.connect(self.db_path)
        
        if task_id:
            cursor = conn.execute('''
                SELECT * FROM task_executions 
                WHERE task_id = ? 
                ORDER BY started_at DESC 
                LIMIT ?
            ''', (task_id, limit))
        else:
            cursor = conn.execute('''
                SELECT * FROM task_executions 
                ORDER BY started_at DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        executions = []
        for row in rows:
            execution = TaskExecution(
                execution_id=row[0],
                task_id=row[1],
                started_at=datetime.fromisoformat(row[2]),
                completed_at=datetime.fromisoformat(row[3]) if row[3] else None,
                status=row[4],
                result=row[5],
                error=row[6],
                duration_seconds=row[7] or 0
            )
            executions.append(execution)
        
        return executions
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        conn = sqlite3.connect(self.db_path)
        
        # Task counts by status
        cursor = conn.execute('''
            SELECT status, COUNT(*) FROM scheduled_tasks GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())
        
        # Execution stats
        cursor = conn.execute('''
            SELECT 
                COUNT(*) as total_executions,
                AVG(duration_seconds) as avg_duration,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions
            FROM task_executions
        ''')
        exec_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'task_counts_by_status': status_counts,
            'total_executions': exec_stats[0],
            'average_duration_seconds': exec_stats[1] or 0,
            'successful_executions': exec_stats[2],
            'failed_executions': exec_stats[3],
            'scheduler_running': self.running
        }

class CronHelper:
    """Helper class for cron expressions"""
    
    @staticmethod
    def every_minute() -> str:
        return "* * * * *"
    
    @staticmethod
    def every_hour() -> str:
        return "0 * * * *"
    
    @staticmethod
    def every_day_at(hour: int, minute: int = 0) -> str:
        return f"{minute} {hour} * * *"
    
    @staticmethod
    def every_week_on(day: str, hour: int = 0, minute: int = 0) -> str:
        days = {
            'monday': '1', 'tuesday': '2', 'wednesday': '3',
            'thursday': '4', 'friday': '5', 'saturday': '6', 'sunday': '0'
        }
        day_num = days.get(day.lower(), '0')
        return f"{minute} {hour} * * {day_num}"
    
    @staticmethod
    def every_month_on_day(day: int, hour: int = 0, minute: int = 0) -> str:
        return f"{minute} {hour} {day} * *"
    
    @staticmethod
    def validate_cron(expression: str) -> bool:
        """Validate a cron expression"""
        try:
            croniter.croniter(expression)
            return True
        except:
            return False

class SchedulerManager:
    """High-level scheduler management interface"""
    
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
    
    async def schedule_recurring_task(self, name: str, description: str, agent_name: str,
                                    cron_expression: str, task_payload: Dict[str, Any],
                                    max_runs: int = None) -> str:
        """Schedule a recurring task using cron expression"""
        task_id = f"recurring_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            description=description,
            schedule_type=ScheduleType.CRON,
            schedule_expression=cron_expression,
            agent_name=agent_name,
            task_payload=task_payload,
            max_runs=max_runs
        )
        
        return await self.scheduler.schedule_task(task)
    
    async def schedule_one_time_task(self, name: str, description: str, agent_name: str,
                                   run_at: datetime, task_payload: Dict[str, Any]) -> str:
        """Schedule a one-time task"""
        task_id = f"once_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            description=description,
            schedule_type=ScheduleType.ONCE,
            schedule_expression=run_at.isoformat(),
            agent_name=agent_name,
            task_payload=task_payload,
            max_runs=1
        )
        
        return await self.scheduler.schedule_task(task)
    
    async def schedule_interval_task(self, name: str, description: str, agent_name: str,
                                   interval_seconds: int, task_payload: Dict[str, Any],
                                   max_runs: int = None) -> str:
        """Schedule a task to run at regular intervals"""
        task_id = f"interval_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            description=description,
            schedule_type=ScheduleType.INTERVAL,
            schedule_expression=str(interval_seconds),
            agent_name=agent_name,
            task_payload=task_payload,
            max_runs=max_runs
        )
        
        return await self.scheduler.schedule_task(task)