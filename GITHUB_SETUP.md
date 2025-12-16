# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **+** icon in the top right → **New repository**
3. Repository settings:
   - **Repository name**: `agents_development` (or your preferred name)
   - **Description**: "AI agents built with Google ADK - multimodal capabilities, tool integration, and multi-agent systems"
   - **Visibility**: Choose **Public** or **Private**
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **Create repository**

## Step 2: Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

```bash
# Navigate to your project
cd /Users/linjia/cursor_ai_space/interview_preparation/ai_ml_interviews/machine_learning/agents_development

# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/agents_development.git

# Or if you prefer SSH:
# git remote add origin git@github.com:YOUR_USERNAME/agents_development.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 3: Verify

1. Go to your repository on GitHub
2. You should see all your files there
3. The README.md should be displayed on the repository homepage

## Alternative: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Install GitHub CLI (if not installed)
# macOS: brew install gh
# Then authenticate: gh auth login

# Create repository and push in one command
cd /Users/linjia/cursor_ai_space/interview_preparation/ai_ml_interviews/machine_learning/agents_development
gh repo create agents_development --public --source=. --remote=origin --push
```

## Important Notes

### Files NOT Included (via .gitignore)

The following files/directories are excluded from the repository:
- `.env` - Contains API keys (never commit this!)
- `__pycache__/` - Python cache files
- `venv/` or `env/` - Virtual environments
- `generated_images/` - Generated image files
- `generated_audio/` - Generated audio files
- `.DS_Store` - macOS system files

### Before Pushing

Make sure your `.env` file is NOT committed:
```bash
# Verify .env is ignored
git check-ignore .env
# Should output: .env

# If .env is tracked, remove it:
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### Adding a License (Optional)

If you want to add a license:

```bash
# Create LICENSE file (choose appropriate license)
# Common choices: MIT, Apache-2.0, GPL-3.0

# Then commit
git add LICENSE
git commit -m "Add LICENSE"
git push
```

## Future Updates

To push future changes:

```bash
# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

## Repository Structure

Your repository will contain:

```
agents_development/
├── README.md                          # Main documentation
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
├── examples/                          # Example agents
│   ├── simple_agent.py
│   ├── tool_agent.py
│   ├── multi_agent.py
│   ├── multimodal_agent.py
│   └── tool_agent_with_mcp.py
├── multimodal_tools/                  # Multimodal capabilities
│   ├── image/
│   ├── audio/
│   └── figures/
├── tools/                              # Custom tools
├── utils/                              # Utility functions
├── agents/                             # Agent configurations
└── Documentation/
    ├── MULTIMODAL_AGENT_COMPLETE_GUIDE.md
    ├── MCP_COMPLETE_GUIDE.md
    ├── CONTEXT_MANAGEMENT_GUIDE.md
    ├── TOOLS_MANAGEMENT_GUIDE.md
    └── MULTI_AGENT_GUIDE.md
```

---

**That's it!** Your repository is now ready on GitHub! 🎉

