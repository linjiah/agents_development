#!/bin/bash
# Activation script for Python 3.12 environment with MCP support

echo "🔄 Activating Python 3.12 environment with MCP support..."
source /Users/linjia/cursor_ai_space/interview_preparation/ml_interview_env_py312/bin/activate

echo "✅ Environment activated!"
echo ""
python --version
echo ""

# Verify MCP
python -c "
try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
    print('✅ MCP support: Available')
except ImportError:
    print('❌ MCP support: Not available')
"

echo ""
echo "📁 Current directory: $(pwd)"
echo ""
echo "Ready to run agents! Try:"
echo "  python examples/tool_agent.py"
echo "  python examples/tool_agent_with_mcp.py"
echo "  python examples/simple_agent.py"
echo ""

