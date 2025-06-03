# memory/memory_system.py
import sqlite3
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    id: str
    agent_name: str
    memory_type: str  # 'conversation', 'knowledge', 'experience', 'fact'
    content: str
    metadata: Dict[str, Any]
    importance: float  # 0.0 to 1.0
    access_count: int
    created_at: datetime
    last_accessed: datetime
    tags: List[str]

class MemoryInterface(ABC):
    """Abstract interface for memory systems"""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, agent_name: str = None, limit: int = 10) -> List[MemoryEntry]:
        pass
    
    @abstractmethod
    async def update_importance(self, entry_id: str, importance: float) -> bool:
        pass
    
    @abstractmethod
    async def forget(self, criteria: Dict[str, Any]) -> int:
        pass

class SQLiteMemorySystem(MemoryInterface):
    """SQLite-based memory system with vector similarity search"""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_name TEXT,
                memory_type TEXT,
                content TEXT,
                metadata TEXT,
                importance REAL,
                access_count INTEGER,
                created_at TEXT,
                last_accessed TEXT,
                tags TEXT,
                embedding BLOB
            )
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_agent_type ON memories(agent_name, memory_type)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, content: str, agent_name: str) -> str:
        """Generate unique ID for memory entry"""
        return hashlib.md5(f"{agent_name}_{content}_{datetime.now().isoformat()}".encode()).hexdigest()
    
    def _simple_embedding(self, text: str) -> bytes:
        """Simple text embedding using character frequency (replace with real embeddings)"""
        # This is a placeholder - in production, use proper embeddings like sentence-transformers
        char_freq = {}
        for char in text.lower():
            char_freq[char] = char_freq.get(char, 0) + 1
        
        # Convert to fixed-size vector
        vector = [char_freq.get(chr(i), 0) for i in range(ord('a'), ord('z') + 1)]
        return pickle.dumps(vector)
    
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry"""
        if not entry.id:
            entry.id = self._generate_id(entry.content, entry.agent_name)
        
        embedding = self._simple_embedding(entry.content)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.agent_name,
            entry.memory_type,
            entry.content,
            json.dumps(entry.metadata),
            entry.importance,
            entry.access_count,
            entry.created_at.isoformat(),
            entry.last_accessed.isoformat(),
            json.dumps(entry.tags),
            embedding
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Stored memory: {entry.id} for agent {entry.agent_name}")
        return entry.id
    
    async def retrieve(self, query: str, agent_name: str = None, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve memories based on query"""
        conn = sqlite3.connect(self.db_path)
        
        # Build SQL query
        sql = "SELECT * FROM memories WHERE 1=1"
        params = []
        
        if agent_name:
            sql += " AND agent_name = ?"
            params.append(agent_name)
        
        if query:
            sql += " AND (content LIKE ? OR tags LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        # Order by importance and recency
        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memory = MemoryEntry(
                id=row[0],
                agent_name=row[1],
                memory_type=row[2],
                content=row[3],
                metadata=json.loads(row[4]),
                importance=row[5],
                access_count=row[6],
                created_at=datetime.fromisoformat(row[7]),
                last_accessed=datetime.fromisoformat(row[8]),
                tags=json.loads(row[9])
            )
            memories.append(memory)
            
            # Update access count
            await self._update_access_count(memory.id)
        
        return memories
    
    async def _update_access_count(self, entry_id: str):
        """Update access count and last accessed time"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            UPDATE memories 
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), entry_id))
        conn.commit()
        conn.close()
    
    async def update_importance(self, entry_id: str, importance: float) -> bool:
        """Update importance score of a memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('UPDATE memories SET importance = ? WHERE id = ?', (importance, entry_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    async def forget(self, criteria: Dict[str, Any]) -> int:
        """Forget memories based on criteria"""
        conn = sqlite3.connect(self.db_path)
        
        # Build delete query based on criteria
        conditions = []
        params = []
        
        if 'older_than_days' in criteria:
            cutoff_date = datetime.now() - timedelta(days=criteria['older_than_days'])
            conditions.append('created_at < ?')
            params.append(cutoff_date.isoformat())
        
        if 'importance_below' in criteria:
            conditions.append('importance < ?')
            params.append(criteria['importance_below'])
        
        if 'agent_name' in criteria:
            conditions.append('agent_name = ?')
            params.append(criteria['agent_name'])
        
        if 'memory_type' in criteria:
            conditions.append('memory_type = ?')
            params.append(criteria['memory_type'])
        
        if conditions:
            sql = f"DELETE FROM memories WHERE {' AND '.join(conditions)}"
            cursor = conn.execute(sql, params)
            deleted_count = cursor.rowcount
            conn.commit()
        else:
            deleted_count = 0
        
        conn.close()
        logger.info(f"Forgot {deleted_count} memories based on criteria: {criteria}")
        return deleted_count
    
    async def get_memory_stats(self, agent_name: str = None) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        
        if agent_name:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(importance) as avg_importance,
                    MAX(created_at) as latest_memory,
                    COUNT(DISTINCT memory_type) as memory_types
                FROM memories WHERE agent_name = ?
            ''', (agent_name,))
        else:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(importance) as avg_importance,
                    MAX(created_at) as latest_memory,
                    COUNT(DISTINCT memory_type) as memory_types
                FROM memories
            ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_memories': row[0],
            'avg_importance': row[1] or 0,
            'latest_memory': row[2],
            'memory_types': row[3]
        }

class MemoryManager:
    """High-level memory management interface"""
    
    def __init__(self, memory_system: MemoryInterface):
        self.memory_system = memory_system
        self.memory_importance_calculator = MemoryImportanceCalculator()
    
    async def remember(self, agent_name: str, content: str, memory_type: str = "general", 
                      metadata: Dict[str, Any] = None, tags: List[str] = None) -> str:
        """Store a new memory with calculated importance"""
        if metadata is None:
            metadata = {}
        if tags is None:
            tags = []
        
        importance = await self.memory_importance_calculator.calculate_importance(
            content, memory_type, metadata
        )
        
        entry = MemoryEntry(
            id="",
            agent_name=agent_name,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            importance=importance,
            access_count=0,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            tags=tags
        )
        
        return await self.memory_system.store(entry)
    
    async def recall(self, agent_name: str, query: str, memory_type: str = None, 
                    limit: int = 10) -> List[MemoryEntry]:
        """Recall relevant memories"""
        memories = await self.memory_system.retrieve(query, agent_name, limit * 2)
        
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
        
        return memories[:limit]
    
    async def consolidate_memories(self, agent_name: str, max_memories: int = 1000):
        """Consolidate memories by removing low-importance old memories"""
        # Get memory statistics
        stats = await self.memory_system.get_memory_stats(agent_name)
        
        if stats['total_memories'] > max_memories:
            # Remove memories with low importance and old age
            forget_criteria = {
                'agent_name': agent_name,
                'importance_below': 0.3,
                'older_than_days': 30
            }
            forgotten_count = await self.memory_system.forget(forget_criteria)
            logger.info(f"Consolidated memories for {agent_name}: removed {forgotten_count} memories")

class MemoryImportanceCalculator:
    """Calculate importance scores for memories"""
    
    async def calculate_importance(self, content: str, memory_type: str, 
                                 metadata: Dict[str, Any]) -> float:
        """Calculate importance score (0.0 to 1.0)"""
        importance = 0.5  # Base importance
        
        # Adjust based on memory type
        type_weights = {
            'knowledge': 0.8,
            'experience': 0.7,
            'conversation': 0.4,
            'fact': 0.6,
            'error': 0.9,  # Errors are important to remember
            'success': 0.8  # Successes are also important
        }
        
        importance *= type_weights.get(memory_type, 0.5)
        
        # Adjust based on content characteristics
        if len(content) > 500:  # Longer content might be more important
            importance += 0.1
        
        if any(keyword in content.lower() for keyword in ['error', 'failed', 'bug', 'issue']):
            importance += 0.2  # Errors are important
        
        if any(keyword in content.lower() for keyword in ['success', 'completed', 'solved']):
            importance += 0.15  # Successes are important
        
        # Adjust based on metadata
        if metadata.get('user_feedback') == 'positive':
            importance += 0.2
        elif metadata.get('user_feedback') == 'negative':
            importance += 0.1  # Negative feedback is still important to learn from
        
        if metadata.get('task_critical', False):
            importance += 0.3
        
        # Ensure importance is within bounds
        return min(max(importance, 0.0), 1.0)

class ConversationMemory:
    """Specialized memory for conversation history"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def add_conversation_turn(self, agent_name: str, user_input: str, 
                                  agent_response: str, context: Dict[str, Any] = None):
        """Add a conversation turn to memory"""
        if context is None:
            context = {}
        
        conversation_content = f"User: {user_input}\nAgent: {agent_response}"
        
        await self.memory_manager.remember(
            agent_name=agent_name,
            content=conversation_content,
            memory_type="conversation",
            metadata={
                'user_input': user_input,
                'agent_response': agent_response,
                'context': context,
                'turn_timestamp': datetime.now().isoformat()
            },
            tags=['conversation', 'dialogue']
        )
    
    async def get_conversation_history(self, agent_name: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        memories = await self.memory_manager.recall(
            agent_name=agent_name,
            query="",
            memory_type="conversation",
            limit=limit
        )
        
        history = []
        for memory in reversed(memories):  # Most recent first
            if 'user_input' in memory.metadata and 'agent_response' in memory.metadata:
                history.append({
                    'user': memory.metadata['user_input'],
                    'agent': memory.metadata['agent_response'],
                    'timestamp': memory.created_at.isoformat()
                })
        
        return history

class KnowledgeMemory:
    """Specialized memory for knowledge and facts"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def add_knowledge(self, agent_name: str, topic: str, information: str, 
                           source: str = None, confidence: float = 1.0):
        """Add knowledge to memory"""
        metadata = {
            'topic': topic,
            'confidence': confidence,
            'knowledge_type': 'factual'
        }
        
        if source:
            metadata['source'] = source
        
        await self.memory_manager.remember(
            agent_name=agent_name,
            content=f"Topic: {topic}\nInformation: {information}",
            memory_type="knowledge",
            metadata=metadata,
            tags=[topic.lower(), 'knowledge', 'fact']
        )
    
    async def query_knowledge(self, agent_name: str, topic: str, limit: int = 5) -> List[str]:
        """Query knowledge about a specific topic"""
        memories = await self.memory_manager.recall(
            agent_name=agent_name,
            query=topic,
            memory_type="knowledge",
            limit=limit
        )
        
        return [memory.content for memory in memories]

class ExperienceMemory:
    """Specialized memory for experiences and learning"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def add_experience(self, agent_name: str, task_type: str, approach: str, 
                           outcome: str, success: bool, lessons_learned: str = None):
        """Add an experience to memory"""
        content = f"Task: {task_type}\nApproach: {approach}\nOutcome: {outcome}"
        if lessons_learned:
            content += f"\nLessons: {lessons_learned}"
        
        metadata = {
            'task_type': task_type,
            'approach': approach,
            'outcome': outcome,
            'success': success,
            'experience_type': 'task_execution'
        }
        
        if lessons_learned:
            metadata['lessons_learned'] = lessons_learned
        
        memory_type = "success" if success else "error"
        
        await self.memory_manager.remember(
            agent_name=agent_name,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            tags=[task_type.lower(), 'experience', memory_type]
        )
    
    async def get_similar_experiences(self, agent_name: str, task_type: str, 
                                    limit: int = 5) -> List[MemoryEntry]:
        """Get experiences similar to current task"""
        return await self.memory_manager.recall(
            agent_name=agent_name,
            query=task_type,
            memory_type=None,  # Include both success and error experiences
            limit=limit
        )