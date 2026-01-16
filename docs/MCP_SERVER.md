# BabelDOC MCP Server

The BabelDOC MCP (Model Context Protocol) Server allows AI assistants like Claude to translate PDF documents directly through natural language commands.

## Features

- **PDF Translation**: Translate PDF documents between multiple languages
- **Multiple Translation Services**: Support for OpenRouter and OpenAI
- **Bilingual Output**: Generate side-by-side original and translated PDFs
- **Configurable Options**: Control pages, output format, watermarks, and more

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- [Claude Code CLI](https://claude.ai/claude-code) installed
- An API key from [OpenRouter](https://openrouter.ai/) or [OpenAI](https://platform.openai.com/)

## Installation

### Step 1: Clone and Install BabelDOC

```bash
# Clone the repository
git clone https://github.com/funstory-ai/BabelDOC
cd BabelDOC

# Install dependencies with uv
uv sync
```

### Step 2: Verify MCP Server Installation

```bash
# Test that the MCP server module loads correctly
uv run python -c "from babeldoc.mcp_server.server import server; print('MCP server ready')"
```

### Step 3: Get Your API Key

#### Option A: OpenRouter (Recommended)

1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Navigate to "Keys" in your dashboard
4. Create a new API key
5. Copy the key (starts with `sk-or-`)

#### Option B: OpenAI

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Navigate to API Keys
3. Create a new secret key
4. Copy the key (starts with `sk-`)

### Step 4: Add MCP Server to Claude Code

Run the following command, replacing the placeholder values with your actual credentials:

#### For OpenRouter:

```bash
claude mcp add babeldoc -s user \
  -e OPENROUTER_API_KEY=your-openrouter-api-key-here \
  -e OPENROUTER_BASE_URL=https://openrouter.ai/api/v1 \
  -e OPENROUTER_MODEL=google/gemini-2.5-flash \
  -- uv run --directory /path/to/BabelDOC babeldoc-mcp
```

#### For OpenAI:

```bash
claude mcp add babeldoc -s user \
  -e OPENAI_API_KEY=your-openai-api-key-here \
  -e OPENAI_MODEL=gpt-4o-mini \
  -- uv run --directory /path/to/BabelDOC babeldoc-mcp
```

**Important**: Replace `/path/to/BabelDOC` with the actual path where you cloned the repository.

### Step 5: Verify Installation

```bash
# Check that the server is connected
claude mcp list

# You should see:
# babeldoc: ... - ✓ Connected
```

To see full configuration details:

```bash
claude mcp get babeldoc
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | API key for OpenRouter | - |
| `OPENROUTER_BASE_URL` | OpenRouter API endpoint | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | Model to use via OpenRouter | `google/gemini-2.5-flash` |
| `OPENAI_API_KEY` | API key for OpenAI | - |
| `OPENAI_BASE_URL` | OpenAI API endpoint | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model to use via OpenAI | `gpt-4o-mini` |

### Recommended Models

#### Via OpenRouter:
- `google/gemini-2.5-flash` - Fast and cost-effective
- `google/gemini-2.5-pro` - Higher quality
- `anthropic/claude-3.5-sonnet` - Excellent translation quality
- `openai/gpt-4o-mini` - Good balance of speed and quality

#### Via OpenAI:
- `gpt-4o-mini` - Fast and affordable
- `gpt-4o` - Higher quality translations

## Usage

Once installed, you can use natural language commands in Claude Code to translate PDFs:

### Basic Translation

```
Translate /path/to/document.pdf to Vietnamese
```

### Specify Languages

```
Translate /path/to/document.pdf from English to Chinese
```

### Translate Specific Pages

```
Translate pages 1-5 of /path/to/document.pdf to Japanese
```

### Custom Output Directory

```
Translate /path/to/document.pdf to Korean and save to /output/folder
```

### Check Service Status

```
Check the BabelDOC translation service status
```

## Available MCP Tools

### `translate_pdf`

Translates a PDF document.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_file` | string | Yes | Absolute path to the PDF file |
| `output_dir` | string | No | Output directory (default: same as input) |
| `lang_in` | string | No | Source language code (default: `en`) |
| `lang_out` | string | No | Target language code (default: `zh`) |
| `pages` | string | No | Pages to translate (e.g., `1-5`, `1,3,5`) |
| `no_dual` | boolean | No | Skip bilingual output (default: `false`) |
| `no_mono` | boolean | No | Skip monolingual output (default: `false`) |
| `service` | string | No | `openrouter` or `openai` (default: `openrouter`) |
| `model` | string | No | Override the default model |
| `qps` | integer | No | API rate limit (default: `4`) |
| `watermark` | boolean | No | Add watermark (default: `true`) |

### `get_translation_status`

Returns service configuration and supported languages.

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `zh` | Chinese (Simplified) |
| `zh-TW` | Chinese (Traditional) |
| `vi` | Vietnamese |
| `ja` | Japanese |
| `ko` | Korean |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `pt` | Portuguese |
| `ru` | Russian |
| `ar` | Arabic |
| `th` | Thai |
| `id` | Indonesian |

## Output Files

After translation, BabelDOC generates:

- `{filename}.{lang}.mono.pdf` - Monolingual translated PDF
- `{filename}.{lang}.dual.pdf` - Bilingual side-by-side PDF

## Troubleshooting

### Server Not Connected

```bash
# Remove and re-add the server
claude mcp remove babeldoc
claude mcp add babeldoc -s user \
  -e OPENROUTER_API_KEY=your-key \
  -- uv run --directory /path/to/BabelDOC babeldoc-mcp
```

### API Key Not Working

1. Verify your API key is valid at the provider's dashboard
2. Check that the environment variable is correctly set:
   ```bash
   claude mcp get babeldoc
   ```
3. Ensure you have sufficient credits/quota

### Translation Fails

1. Check that the input file exists and is a valid PDF
2. Ensure the output directory is writable
3. Try with `--pages "1"` first to test with a single page

### Module Not Found

```bash
# Reinstall dependencies
cd /path/to/BabelDOC
uv sync
```

## Uninstall

To remove the MCP server from Claude Code:

```bash
claude mcp remove babeldoc
```

## CLI Usage (Alternative)

You can also use BabelDOC directly from the command line:

```bash
# Using OpenRouter
uv run babeldoc --openrouter \
  --openrouter-api-key "your-key" \
  --openrouter-model "google/gemini-2.5-flash" \
  --lang-in en \
  --lang-out vi \
  --files /path/to/document.pdf \
  --output /path/to/output

# Using OpenAI
uv run babeldoc --openai \
  --openai-api-key "your-key" \
  --openai-model "gpt-4o-mini" \
  --lang-in en \
  --lang-out zh \
  --files /path/to/document.pdf
```

## Security Notes

- API keys are stored in `~/.claude.json` for the MCP server
- This file is user-specific and not committed to version control
- Never commit API keys to the repository
- Consider using environment variables in production environments

## License

This MCP server is part of BabelDOC and is licensed under AGPL-3.0.
