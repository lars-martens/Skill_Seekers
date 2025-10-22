#!/usr/bin/env python3
"""
Skill Seeker MCP Server
Model Context Protocol server for generating Claude AI skills from documentation
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ Error: mcp package not installed")
    print("Install with: pip install mcp")
    sys.exit(1)


# Initialize MCP server
app = Server("skill-seeker")

# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent / "cli"


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="generate_config",
            description="Generate a config file for documentation scraping. Interactively creates a JSON config for any documentation website.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill name (lowercase, alphanumeric, hyphens, underscores)",
                    },
                    "url": {
                        "type": "string",
                        "description": "Base documentation URL (must include http:// or https://)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of when to use this skill",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum pages to scrape (default: 100)",
                        "default": 100,
                    },
                    "rate_limit": {
                        "type": "number",
                        "description": "Delay between requests in seconds (default: 0.5)",
                        "default": 0.5,
                    },
                },
                "required": ["name", "url", "description"],
            },
        ),
        Tool(
            name="estimate_pages",
            description="Estimate how many pages will be scraped from a config. Fast preview without downloading content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/react.json)",
                    },
                    "max_discovery": {
                        "type": "integer",
                        "description": "Maximum pages to discover during estimation (default: 1000)",
                        "default": 1000,
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="scrape_docs",
            description="Scrape documentation and build Claude skill. Creates SKILL.md and reference files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/react.json)",
                    },
                    "enhance_local": {
                        "type": "boolean",
                        "description": "Open terminal for local enhancement with Claude Code (default: false)",
                        "default": False,
                    },
                    "skip_scrape": {
                        "type": "boolean",
                        "description": "Skip scraping, use cached data (default: false)",
                        "default": False,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview what will be scraped without saving (default: false)",
                        "default": False,
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="package_skill",
            description="Package a skill directory into a .zip file ready for Claude upload. Automatically uploads if ANTHROPIC_API_KEY is set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_dir": {
                        "type": "string",
                        "description": "Path to skill directory (e.g., output/react/)",
                    },
                    "auto_upload": {
                        "type": "boolean",
                        "description": "Try to upload automatically if API key is available (default: true). If false, only package without upload attempt.",
                        "default": True,
                    },
                },
                "required": ["skill_dir"],
            },
        ),
        Tool(
            name="upload_skill",
            description="Upload a skill .zip file to Claude automatically (requires ANTHROPIC_API_KEY)",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_zip": {
                        "type": "string",
                        "description": "Path to skill .zip file (e.g., output/react.zip)",
                    },
                },
                "required": ["skill_zip"],
            },
        ),
        Tool(
            name="list_configs",
            description="List all available preset configurations.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="validate_config",
            description="Validate a config file for errors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file",
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="split_config",
            description="Split large documentation config into multiple focused skills. For 10K+ page documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Path to config JSON file (e.g., configs/godot.json)",
                    },
                    "strategy": {
                        "type": "string",
                        "description": "Split strategy: auto, none, category, router, size (default: auto)",
                        "default": "auto",
                    },
                    "target_pages": {
                        "type": "integer",
                        "description": "Target pages per skill (default: 5000)",
                        "default": 5000,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview without saving files (default: false)",
                        "default": False,
                    },
                },
                "required": ["config_path"],
            },
        ),
        Tool(
            name="generate_router",
            description="Generate router/hub skill for split documentation. Creates intelligent routing to sub-skills.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_pattern": {
                        "type": "string",
                        "description": "Config pattern for sub-skills (e.g., 'configs/godot-*.json')",
                    },
                    "router_name": {
                        "type": "string",
                        "description": "Router skill name (optional, inferred from configs)",
                    },
                },
                "required": ["config_pattern"],
            },
        ),
        Tool(
            name="fetch_knowledge",
            description="Fetch and download knowledge packages from the Skill Seeker API. List available skills, search by category, or download specific packages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'list', 'search', 'download', 'details'",
                        "enum": ["list", "search", "download", "details"],
                    },
                    "api_url": {
                        "type": "string",
                        "description": "API base URL (default: http://localhost:5000)",
                        "default": "http://localhost:5000",
                    },
                    "knowledge_id": {
                        "type": "integer",
                        "description": "Knowledge package ID (for 'download' or 'details' actions)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (for 'list' or 'search' actions)",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Filter by framework (for 'list' or 'search' actions)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["action"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "generate_config":
            return await generate_config_tool(arguments)
        elif name == "estimate_pages":
            return await estimate_pages_tool(arguments)
        elif name == "scrape_docs":
            return await scrape_docs_tool(arguments)
        elif name == "package_skill":
            return await package_skill_tool(arguments)
        elif name == "upload_skill":
            return await upload_skill_tool(arguments)
        elif name == "list_configs":
            return await list_configs_tool(arguments)
        elif name == "validate_config":
            return await validate_config_tool(arguments)
        elif name == "split_config":
            return await split_config_tool(arguments)
        elif name == "generate_router":
            return await generate_router_tool(arguments)
        elif name == "fetch_knowledge":
            return await fetch_knowledge_tool(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def generate_config_tool(args: dict) -> list[TextContent]:
    """Generate a config file"""
    name = args["name"]
    url = args["url"]
    description = args["description"]
    max_pages = args.get("max_pages", 100)
    rate_limit = args.get("rate_limit", 0.5)

    # Create config
    config = {
        "name": name,
        "description": description,
        "base_url": url,
        "selectors": {
            "main_content": "article",
            "title": "h1",
            "code_blocks": "pre code"
        },
        "url_patterns": {
            "include": [],
            "exclude": []
        },
        "categories": {},
        "rate_limit": rate_limit,
        "max_pages": max_pages
    }

    # Save to configs directory
    config_path = Path("configs") / f"{name}.json"
    config_path.parent.mkdir(exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    result = f"""✅ Config created: {config_path}

Configuration:
  Name: {name}
  URL: {url}
  Max pages: {max_pages}
  Rate limit: {rate_limit}s

Next steps:
  1. Review/edit config: cat {config_path}
  2. Estimate pages: Use estimate_pages tool
  3. Scrape docs: Use scrape_docs tool

Note: Default selectors may need adjustment for your documentation site.
"""

    return [TextContent(type="text", text=result)]


async def estimate_pages_tool(args: dict) -> list[TextContent]:
    """Estimate page count"""
    config_path = args["config_path"]
    max_discovery = args.get("max_discovery", 1000)

    # Run estimate_pages.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "estimate_pages.py"),
        config_path,
        "--max-discovery", str(max_discovery)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}")]


async def scrape_docs_tool(args: dict) -> list[TextContent]:
    """Scrape documentation"""
    config_path = args["config_path"]
    enhance_local = args.get("enhance_local", False)
    skip_scrape = args.get("skip_scrape", False)
    dry_run = args.get("dry_run", False)

    # Build command
    cmd = [
        sys.executable,
        str(CLI_DIR / "doc_scraper.py"),
        "--config", config_path
    ]

    if enhance_local:
        cmd.append("--enhance-local")
    if skip_scrape:
        cmd.append("--skip-scrape")
    if dry_run:
        cmd.append("--dry-run")

    # Run doc_scraper.py
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}\n{result.stdout}")]


async def package_skill_tool(args: dict) -> list[TextContent]:
    """Package skill to .zip and optionally auto-upload"""
    skill_dir = args["skill_dir"]
    auto_upload = args.get("auto_upload", True)

    # Check if API key exists - only upload if available
    has_api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    should_upload = auto_upload and has_api_key

    # Run package_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "package_skill.py"),
        skill_dir,
        "--no-open"  # Don't open folder in MCP context
    ]

    # Add upload flag only if we have API key
    if should_upload:
        cmd.append("--upload")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        output = result.stdout

        if should_upload:
            # Upload succeeded
            output += "\n\n✅ Skill packaged and uploaded automatically!"
            output += "\n   Your skill is now available in Claude!"
        elif auto_upload and not has_api_key:
            # User wanted upload but no API key
            output += "\n\n📝 Skill packaged successfully!"
            output += "\n"
            output += "\n💡 To enable automatic upload:"
            output += "\n   1. Get API key from https://console.anthropic.com/"
            output += "\n   2. Set: export ANTHROPIC_API_KEY=sk-ant-..."
            output += "\n"
            output += "\n📤 Manual upload:"
            output += "\n   1. Find the .zip file in your output/ folder"
            output += "\n   2. Go to https://claude.ai/skills"
            output += "\n   3. Click 'Upload Skill' and select the .zip file"
        else:
            # auto_upload=False, just packaged
            output += "\n\n✅ Skill packaged successfully!"
            output += "\n   Upload manually to https://claude.ai/skills"

        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}\n{result.stdout}")]


async def upload_skill_tool(args: dict) -> list[TextContent]:
    """Upload skill .zip to Claude"""
    skill_zip = args["skill_zip"]

    # Run upload_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "upload_skill.py"),
        skill_zip
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}\n{result.stdout}")]


async def list_configs_tool(args: dict) -> list[TextContent]:
    """List available configs"""
    configs_dir = Path("configs")

    if not configs_dir.exists():
        return [TextContent(type="text", text="No configs directory found")]

    configs = list(configs_dir.glob("*.json"))

    if not configs:
        return [TextContent(type="text", text="No config files found")]

    result = "📋 Available Configs:\n\n"

    for config_file in sorted(configs):
        try:
            with open(config_file) as f:
                config = json.load(f)
                name = config.get("name", config_file.stem)
                desc = config.get("description", "No description")
                url = config.get("base_url", "")

                result += f"  • {config_file.name}\n"
                result += f"    Name: {name}\n"
                result += f"    URL: {url}\n"
                result += f"    Description: {desc}\n\n"
        except Exception as e:
            result += f"  • {config_file.name} - Error reading: {e}\n\n"

    return [TextContent(type="text", text=result)]


async def validate_config_tool(args: dict) -> list[TextContent]:
    """Validate a config file"""
    config_path = args["config_path"]

    # Import validation function
    sys.path.insert(0, str(CLI_DIR))
    from doc_scraper import validate_config
    import json

    try:
        # Load config manually to avoid sys.exit() calls
        if not Path(config_path).exists():
            return [TextContent(type="text", text=f"❌ Error: Config file not found: {config_path}")]

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Validate config - returns (errors, warnings) tuple
        errors, warnings = validate_config(config)

        if errors:
            result = f"❌ Config validation failed:\n\n"
            for error in errors:
                result += f"  • {error}\n"
        else:
            result = f"✅ Config is valid!\n\n"
            result += f"  Name: {config['name']}\n"
            result += f"  Base URL: {config['base_url']}\n"
            result += f"  Max pages: {config.get('max_pages', 'Not set')}\n"
            result += f"  Rate limit: {config.get('rate_limit', 'Not set')}s\n"

            if warnings:
                result += f"\n⚠️  Warnings:\n"
                for warning in warnings:
                    result += f"  • {warning}\n"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def split_config_tool(args: dict) -> list[TextContent]:
    """Split large config into multiple focused configs"""
    config_path = args["config_path"]
    strategy = args.get("strategy", "auto")
    target_pages = args.get("target_pages", 5000)
    dry_run = args.get("dry_run", False)

    # Run split_config.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "split_config.py"),
        config_path,
        "--strategy", strategy,
        "--target-pages", str(target_pages)
    ]

    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}\n\n{result.stdout}")]


async def generate_router_tool(args: dict) -> list[TextContent]:
    """Generate router skill for split documentation"""
    import glob

    config_pattern = args["config_pattern"]
    router_name = args.get("router_name")

    # Expand glob pattern
    config_files = glob.glob(config_pattern)

    if not config_files:
        return [TextContent(type="text", text=f"❌ No config files match pattern: {config_pattern}")]

    # Run generate_router.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "generate_router.py"),
    ] + config_files

    if router_name:
        cmd.extend(["--name", router_name])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return [TextContent(type="text", text=result.stdout)]
    else:
        return [TextContent(type="text", text=f"Error: {result.stderr}\n\n{result.stdout}")]


async def fetch_knowledge_tool(args: dict) -> list[TextContent]:
    """Fetch knowledge packages from API"""
    import requests

    action = args["action"]
    api_url = args.get("api_url", "http://localhost:5000")

    try:
        if action == "list":
            # List all knowledge packages
            category = args.get("category")
            framework = args.get("framework")
            limit = args.get("limit", 10)

            params = {"limit": limit}
            if category:
                params["category"] = category
            if framework:
                params["framework"] = framework

            response = requests.get(f"{api_url}/api/knowledge/list", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                return [TextContent(type="text", text="No knowledge packages found.")]

            output = f"📚 Available Knowledge Packages ({data['count']} results):\n\n"

            for pkg in results:
                output += f"  [{pkg['id']}] {pkg['title']}\n"
                output += f"      Category: {pkg['category']}"
                if pkg.get('framework'):
                    output += f" | Framework: {pkg['framework']}"
                if pkg.get('version'):
                    output += f" | Version: {pkg['version']}"
                output += f"\n      Downloads: {pkg['downloads']}"
                if pkg.get('rating_avg'):
                    output += f" | Rating: {pkg['rating_avg']}/5.0"
                output += f"\n      Size: {pkg['file_size'] // 1024} KB"
                if pkg.get('page_count'):
                    output += f" | Pages: {pkg['page_count']}"
                output += f"\n      {pkg['description'][:100]}...\n\n"

            output += f"\n💡 Use action='download' with knowledge_id to download a package"
            output += f"\n💡 Use action='details' with knowledge_id for full information"

            return [TextContent(type="text", text=output)]

        elif action == "details":
            # Get detailed information about a package
            knowledge_id = args.get("knowledge_id")
            if not knowledge_id:
                return [TextContent(type="text", text="❌ Error: knowledge_id is required for 'details' action")]

            response = requests.get(f"{api_url}/api/knowledge/{knowledge_id}", timeout=10)
            response.raise_for_status()

            pkg = response.json()

            output = f"📋 Knowledge Package Details:\n\n"
            output += f"  ID: {pkg['id']}\n"
            output += f"  Name: {pkg['name']}\n"
            output += f"  Title: {pkg['title']}\n"
            output += f"  Description: {pkg['description']}\n"
            output += f"  Category: {pkg['category']}\n"
            if pkg.get('framework'):
                output += f"  Framework: {pkg['framework']}\n"
            if pkg.get('version'):
                output += f"  Version: {pkg['version']}\n"
            output += f"  File Size: {pkg['file_size'] // 1024} KB\n"
            if pkg.get('page_count'):
                output += f"  Page Count: {pkg['page_count']}\n"
            output += f"  Upload Date: {pkg['upload_date']}\n"
            if pkg.get('uploader_name'):
                output += f"  Uploader: {pkg['uploader_name']}\n"
            if pkg.get('source_url'):
                output += f"  Source URL: {pkg['source_url']}\n"
            output += f"  Downloads: {pkg['downloads']}\n"
            if pkg.get('rating_avg'):
                output += f"  Rating: {pkg['rating_avg']}/5.0 ({pkg['rating_count']} ratings)\n"
            output += f"  Status: {pkg['status']}\n"
            if pkg.get('tags'):
                output += f"  Tags: {pkg['tags']}\n"

            output += f"\n💡 Use action='download' to download this package"

            return [TextContent(type="text", text=output)]

        elif action == "download":
            # Download a specific package
            knowledge_id = args.get("knowledge_id")
            if not knowledge_id:
                return [TextContent(type="text", text="❌ Error: knowledge_id is required for 'download' action")]

            # Get package details first
            details_response = requests.get(f"{api_url}/api/knowledge/{knowledge_id}", timeout=10)
            details_response.raise_for_status()
            pkg = details_response.json()

            # Download the file
            download_response = requests.get(f"{api_url}/api/knowledge/{knowledge_id}/download", timeout=30)
            download_response.raise_for_status()

            # Save to downloads directory
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)

            filename = f"{pkg['name']}.zip"
            filepath = downloads_dir / filename

            with open(filepath, 'wb') as f:
                f.write(download_response.content)

            output = f"✅ Downloaded: {pkg['title']}\n\n"
            output += f"  Saved to: {filepath}\n"
            output += f"  Size: {len(download_response.content) // 1024} KB\n"
            output += f"  Category: {pkg['category']}\n"
            output += f"\n📤 To use this skill:\n"
            output += f"  1. Upload to Claude at https://claude.ai/skills\n"
            output += f"  2. Or unzip and customize: unzip {filepath}\n"

            return [TextContent(type="text", text=output)]

        elif action == "search":
            # Search is same as list with filters
            return await fetch_knowledge_tool({**args, "action": "list"})

        else:
            return [TextContent(type="text", text=f"❌ Unknown action: {action}. Use: list, search, download, details")]

    except requests.exceptions.ConnectionError:
        return [TextContent(type="text", text=f"❌ Error: Could not connect to API at {api_url}\n\nMake sure the API server is running:\n  python3 api/knowledge_api.py")]
    except requests.exceptions.HTTPError as e:
        return [TextContent(type="text", text=f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
