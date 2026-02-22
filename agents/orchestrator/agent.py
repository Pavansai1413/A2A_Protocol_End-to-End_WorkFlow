try:
    # Package import (preferred)
    from .orchestrator_agent import orchestrator_agent
except ImportError:
    # Top-level import (when ADK adds this folder to sys.path and imports `agent`)
    from orchestrator_agent import orchestrator_agent

# ADK Web expects this
root_agent = orchestrator_agent

# ADK Eval (your version) expects agent_module.agent.root_agent
class _AgentShim:
    pass

agent = _AgentShim()
agent.root_agent = root_agent