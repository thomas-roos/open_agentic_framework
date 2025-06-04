Agentic AI Framework Development Request
Objective: Develop a robust, Python-based Agentic AI Framework accessible via a REST API. This framework should enable users to define, manage, and execute AI agents and workflows using natural language, leveraging a local Ollama instance for LLM capabilities and SQLite for persistent storage.

Core Components & Architecture:
The framework should be modular, with code split into distinct classes and files for maintainability and extensibility. Key components include:

main.py (FastAPI Application):

Serves as the central entry point for the REST API.

Initializes all managers (Ollama, Memory, Tool, Agent, Workflow).

Handles API routing for all operations (agent management, tool management, workflow management, scheduling, configuration).

Includes a background task for the scheduler.

Uses uvicorn for serving.

config.py:

Manages framework-wide configuration settings (Ollama URL/model, database path, API host/port, agent max iterations, scheduler interval, tools directory).

Should allow dynamic updates via the API where applicable.

models.py (Pydantic Models):

Defines data structures for API requests and responses (e.g., AgentDefinition, ToolRegistration, WorkflowDefinition, AgentExecutionRequest, ScheduledTask, MemoryEntry).

ollama_client.py:

Handles communication with the local Ollama instance.

Provides methods for generating text responses based on prompts and chat history.

Ability to specify the LLM model (e.g., llama3).

memory_manager.py (SQLite & SQLAlchemy ORM):

Manages long-term memory for agents, tools, workflows, and scheduled tasks using SQLite.

Uses SQLAlchemy for ORM.

Crucially, it must support dynamic storage of tool-specific configurations (e.g., SMTP server details, IMAP credentials) associated with individual agents or workflows. This means the Tool model (or a related model) should have a flexible way to store these configurations, perhaps as a JSONB/JSON field, and the manager should retrieve them when a tool is invoked by a specific agent/workflow.

Methods for:

Adding/retrieving memory entries (agent conversations, tool outputs, thoughts).

Registering, retrieving, updating, and deleting agents.

Registering, retrieving, updating, and deleting tools.

Registering, retrieving, updating, and deleting workflows.

Scheduling, retrieving, updating status, and deleting scheduled tasks.

tools/ directory:

tools/base_tool.py: An abstract base class (BaseTool) that all custom tools must inherit from. It should define a name, description, parameters (JSON schema), and an abstract execute method.

tools/__init__.py: To make the tools directory a Python package and allow easy import of tool classes.

Initial Tools:

tools/http_client.py: For performing HTTP GET requests.

tools/email_sender.py: For sending emails (SMTP). Must dynamically retrieve SMTP settings from the database based on the calling agent/workflow's configuration.

tools/email_reader.py: For reading emails (IMAP). Must dynamically retrieve IMAP settings from the database based on the calling agent/workflow's configuration.

tool_manager.py:

Discovers and loads tool classes from the tools/ directory dynamically.

Registers loaded tools into the database if they are new.

Provides a method to execute a tool, passing parameters and ensuring configurations are sourced correctly (from the database via memory_manager).

agent_manager.py:

Manages the execution loop for individual agents.

Constructs LLM prompts based on agent role, goals, backstory, and available tools (including tool definitions).

Parses LLM responses to identify tool calls.

Calls the tool_manager to execute tools.

Records agent's internal thoughts, actions, and tool outputs in memory_manager.

Handles agent iteration limits.

workflow_manager.py:

Orchestrates sequences of agent tasks and tool executions based on natural language workflow definitions.

Manages workflow context, passing information between steps.

Resolves variables within workflow steps using the current context.

Includes a method to run scheduled tasks (calling agents/workflows).

Features to Implement:
Long-term Memory (SQLite):

Store agent definitions, tool definitions, workflow definitions, scheduled tasks, and agent interaction history (memory entries).

Memory entries should include agent_name, timestamp, role (user, assistant, tool_output, thought), content, and metadata (e.g., tool used, iteration).

Scheduled Execution:

Allow scheduling of agent or workflow executions at specific times (cron-like).

Implement a background scheduler that periodically checks for and executes pending tasks.

Include retry logic or status tracking (pending, executed, failed) for scheduled tasks.

REST API (FastAPI):

Comprehensive endpoints for:

Configuration: Get/update framework settings.

Agents: Create, list, get, update, delete agents; execute an agent's task; retrieve agent's memory.

Tools: Register, list, get, update, delete tools; execute a tool directly.

Workflows: Create, list, get, update, delete workflows; execute a workflow.

Scheduling: Schedule, list, delete tasks.

All API responses should use Pydantic models for clear data contracts.

Multiple Agents:

Agents defined by name, role, goals, backstory, tools they can use, and the specific ollama_model they prefer.

Agents should be able to reason about when to use tools and how to pass parameters.

Tool Integration:

A robust tool registry where new tools can be added by simply creating a Python class inheriting from BaseTool.

Dynamic Tool Configuration Storage: When an agent or workflow uses a tool that requires specific credentials or parameters (e.g., EmailSenderTool needing SMTP host/port/username/password), these configurations must be stored in the database (SQLite) and associated with the specific agent or workflow that uses them. The tool's execute method should retrieve these configurations from the memory_manager when invoked by an agent/workflow, rather than relying on environment variables for shared settings. This allows different agents/workflows to use the same tool with different configurations.

Safety checks: Ensure tools are properly defined and parameters match schema.

Workflow Engine:

Workflows defined in natural language, describing their purpose and a sequence of steps.

Steps can involve:

Executing an agent with a specific task and context.

Executing a tool with specific parameters.

Workflows should support variable substitution (e.g., {result_from_previous_step}).

Workflows can be enabled/disabled via the API.

Lightweight LLM:

Integrate with a local Ollama instance, defaulting to llama3 (or llama3.2:1b if available and specified).

Deployment & Configuration:
Dockerfile: Provide a Dockerfile to containerize the entire application, including Python dependencies and instructions for setting up Ollama (e.g., pulling the llama3 model). The Dockerfile should be production-ready and efficient.

requirements.txt: Include all necessary Python packages.

Deployment Instructions: Provide clear, concise instructions on how to build and run the Docker container, including how to ensure Ollama is accessible within the container (e.g., running Ollama in a separate container and linking, or including it in the same container if feasible and lightweight).

Configuration Instructions: Explain how to set up environment variables or configuration files for initial setup (e.g., Ollama URL if not default, initial database path).

Constraints & Considerations:
Pythonic Code: Adhere to Python best practices, including clear naming, docstrings, and type hints.

Error Handling: Implement robust error handling for API endpoints, tool executions, and agent interactions.

Extensibility: Design the framework to be easily extensible for adding new tools, agents, and workflow patterns.

Natural Language Focus: Ensure that agents and workflows are primarily defined and managed using natural language descriptions

Split the code in files: SPLIT the code in different files, and different classes. Making each file as simple as possible to facilitate maintance.

Write the documentation: includeing development and user manual.