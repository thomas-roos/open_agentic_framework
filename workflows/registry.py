# workflows/registry.py - Dynamic workflow registry system

import json
import logging
import importlib
import inspect
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class WorkflowBase(ABC):
    """Base class for all workflows"""
    
    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.version: str = "1.0.0"
        self.author: str = ""
        self.tags: List[str] = []
        self.parameters: Dict[str, Any] = {}
        self.enabled: bool = True
        self.created_at: datetime = datetime.now()
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the workflow with given parameters"""
        pass
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate input parameters. Override if needed."""
        return {"valid": True}
    
    def get_info(self) -> Dict[str, Any]:
        """Get workflow information"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat()
        }
    
    async def start(self) -> Dict[str, Any]:
        """Called when workflow is started/enabled"""
        return {"status": "started"}
    
    async def stop(self) -> Dict[str, Any]:
        """Called when workflow is stopped/disabled"""
        return {"status": "stopped"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the workflow"""
        return {"healthy": True}

class WorkflowRegistry:
    """Registry for managing workflows dynamically"""
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = Path(data_dir)
        self.registry_file = self.data_dir / "workflow_registry.json"
        self.workflows_dir = self.data_dir / "workflows"
        
        # In-memory registry
        self.workflows: Dict[str, WorkflowBase] = {}
        self.workflow_configs: Dict[str, Dict[str, Any]] = {}
        self.workflow_endpoints: Dict[str, List[Dict[str, Any]]] = {}
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing workflows
        self._load_registry()
        self._discover_workflows()
    
    def register_workflow(self, workflow_class: Type[WorkflowBase], 
                         config: Optional[Dict[str, Any]] = None,
                         endpoints: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Register a new workflow"""
        try:
            # Create workflow instance
            workflow = workflow_class()
            
            # Validate workflow
            if not workflow.name:
                logger.error(f"Workflow {workflow_class.__name__} must have a name")
                return False
            
            # Store workflow
            self.workflows[workflow.name] = workflow
            self.workflow_configs[workflow.name] = config or {}
            self.workflow_endpoints[workflow.name] = endpoints or []
            
            # Save to registry
            self._save_registry()
            
            logger.info(f"✅ Registered workflow: {workflow.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register workflow {workflow_class.__name__}: {e}")
            return False
    
    def unregister_workflow(self, workflow_name: str) -> bool:
        """Unregister a workflow"""
        try:
            if workflow_name in self.workflows:
                # Stop workflow if running
                workflow = self.workflows[workflow_name]
                asyncio.create_task(workflow.stop())
                
                # Remove from registry
                del self.workflows[workflow_name]
                del self.workflow_configs[workflow_name]
                del self.workflow_endpoints[workflow_name]
                
                # Save registry
                self._save_registry()
                
                logger.info(f"✅ Unregistered workflow: {workflow_name}")
                return True
            else:
                logger.warning(f"Workflow {workflow_name} not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to unregister workflow {workflow_name}: {e}")
            return False
    
    def get_workflow(self, workflow_name: str) -> Optional[WorkflowBase]:
        """Get a workflow by name"""
        return self.workflows.get(workflow_name)
    
    def list_workflows(self, enabled_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """List all registered workflows"""
        workflows = {}
        for name, workflow in self.workflows.items():
            if enabled_only and not workflow.enabled:
                continue
            
            workflows[name] = {
                **workflow.get_info(),
                "config": self.workflow_configs.get(name, {}),
                "endpoints": self.workflow_endpoints.get(name, [])
            }
        
        return workflows
    
    def enable_workflow(self, workflow_name: str) -> bool:
        """Enable a workflow"""
        if workflow_name in self.workflows:
            workflow = self.workflows[workflow_name]
            workflow.enabled = True
            asyncio.create_task(workflow.start())
            self._save_registry()
            logger.info(f"✅ Enabled workflow: {workflow_name}")
            return True
        return False
    
    def disable_workflow(self, workflow_name: str) -> bool:
        """Disable a workflow"""
        if workflow_name in self.workflows:
            workflow = self.workflows[workflow_name]
            workflow.enabled = False
            asyncio.create_task(workflow.stop())
            self._save_registry()
            logger.info(f"🛑 Disabled workflow: {workflow_name}")
            return True
        return False
    
    async def execute_workflow(self, workflow_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_name not in self.workflows:
            return {"error": f"Workflow '{workflow_name}' not found"}
        
        workflow = self.workflows[workflow_name]
        
        if not workflow.enabled:
            return {"error": f"Workflow '{workflow_name}' is disabled"}
        
        try:
            # Validate parameters
            validation = workflow.validate_parameters(**kwargs)
            if not validation.get("valid", False):
                return {"error": f"Invalid parameters: {validation.get('message', 'Unknown error')}"}
            
            # Execute workflow
            result = await workflow.execute(**kwargs)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error executing workflow {workflow_name}: {e}")
            return {"error": str(e)}
    
    def get_workflow_endpoints(self, workflow_name: str) -> List[Dict[str, Any]]:
        """Get custom endpoints for a workflow"""
        return self.workflow_endpoints.get(workflow_name, [])
    
    def get_all_endpoints(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all custom endpoints from all workflows"""
        return self.workflow_endpoints.copy()
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all workflows"""
        results = {}
        for name, workflow in self.workflows.items():
            if workflow.enabled:
                try:
                    results[name] = await workflow.health_check()
                except Exception as e:
                    results[name] = {"healthy": False, "error": str(e)}
            else:
                results[name] = {"healthy": False, "disabled": True}
        
        return results
    
    def _save_registry(self):
        """Save workflow registry to file"""
        try:
            registry_data = {
                "workflows": {},
                "configs": self.workflow_configs,
                "endpoints": self.workflow_endpoints,
                "last_updated": datetime.now().isoformat()
            }
            
            # Save workflow info (not instances)
            for name, workflow in self.workflows.items():
                registry_data["workflows"][name] = {
                    "class_path": f"{workflow.__class__.__module__}.{workflow.__class__.__name__}",
                    "info": workflow.get_info()
                }
            
            with open(self.registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"❌ Failed to save workflow registry: {e}")
    
    def _load_registry(self):
        """Load workflow registry from file"""
        if not self.registry_file.exists():
            return
        
        try:
            with open(self.registry_file, 'r') as f:
                registry_data = json.load(f)
            
            self.workflow_configs = registry_data.get("configs", {})
            self.workflow_endpoints = registry_data.get("endpoints", {})
            
            # Load workflows
            for name, workflow_data in registry_data.get("workflows", {}).items():
                try:
                    class_path = workflow_data["class_path"]
                    module_path, class_name = class_path.rsplit('.', 1)
                    
                    # Import and instantiate
                    module = importlib.import_module(module_path)
                    workflow_class = getattr(module, class_name)
                    workflow = workflow_class()
                    
                    self.workflows[name] = workflow
                    
                except Exception as e:
                    logger.warning(f"Failed to load workflow {name}: {e}")
            
            logger.info(f"✅ Loaded {len(self.workflows)} workflows from registry")
            
        except Exception as e:
            logger.error(f"❌ Failed to load workflow registry: {e}")
    
    def _discover_workflows(self):
        """Auto-discover workflows in the workflows directory"""
        try:
            # Look for workflow files
            workflow_files = []
            
            # Check workflows/predefined/ directory
            predefined_dir = Path("workflows/predefined")
            if predefined_dir.exists():
                workflow_files.extend(predefined_dir.glob("*.py"))
            
            # Check data/workflows/ directory for user-added workflows
            user_workflows_dir = self.workflows_dir
            if user_workflows_dir.exists():
                workflow_files.extend(user_workflows_dir.glob("*.py"))
            
            for workflow_file in workflow_files:
                if workflow_file.name.startswith("__"):
                    continue
                
                try:
                    # Import module
                    module_name = workflow_file.stem
                    if "predefined" in str(workflow_file):
                        module_path = f"workflows.predefined.{module_name}"
                    else:
                        # Add to sys.path and import
                        import sys
                        sys.path.insert(0, str(workflow_file.parent))
                        module_path = module_name
                    
                    module = importlib.import_module(module_path)
                    
                    # Look for workflow classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, WorkflowBase) and 
                            obj != WorkflowBase):
                            
                            # Auto-register if not already registered
                            workflow_instance = obj()
                            if workflow_instance.name and workflow_instance.name not in self.workflows:
                                self.register_workflow(obj)
                                logger.info(f"🔍 Auto-discovered workflow: {workflow_instance.name}")
                
                except Exception as e:
                    logger.warning(f"Failed to discover workflows in {workflow_file}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Failed to discover workflows: {e}")

# Global registry instance
_registry = None

def get_workflow_registry() -> WorkflowRegistry:
    """Get or create global workflow registry"""
    global _registry
    if _registry is None:
        _registry = WorkflowRegistry()
    return _registry