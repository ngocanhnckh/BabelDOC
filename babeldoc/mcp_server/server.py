#!/usr/bin/env python3
"""
BabelDOC MCP Server

A Model Context Protocol (MCP) server that provides PDF translation capabilities
using BabelDOC with support for OpenAI and OpenRouter translation services.
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

# BabelDOC imports
import babeldoc.format.pdf.high_level
from babeldoc.format.pdf.translation_config import TranslationConfig
from babeldoc.format.pdf.translation_config import WatermarkOutputMode
from babeldoc.translator.translator import OpenAITranslator
from babeldoc.translator.translator import set_translate_rate_limiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
for noisy_logger in ["httpx", "openai", "httpcore", "http11", "pdfminer", "peewee"]:
    logging.getLogger(noisy_logger).setLevel(logging.CRITICAL)
    logging.getLogger(noisy_logger).propagate = False

# Create MCP server instance
server = Server("babeldoc-mcp")


def resolve_path_with_unicode_normalization(file_path: str) -> Path | None:
    """
    Resolve a file path, trying both NFC and NFD Unicode normalization forms.

    Some filesystems (especially on macOS/Linux) store filenames in NFD form,
    while applications may pass NFC form. This function tries both.
    """
    path = Path(file_path)
    if path.exists():
        return path

    # Try NFC normalization
    nfc_path = Path(unicodedata.normalize("NFC", file_path))
    if nfc_path.exists():
        return nfc_path

    # Try NFD normalization
    nfd_path = Path(unicodedata.normalize("NFD", file_path))
    if nfd_path.exists():
        return nfd_path

    # Try to find the file by listing the directory and matching
    parent = path.parent
    if parent.exists():
        target_name_nfc = unicodedata.normalize("NFC", path.name)
        target_name_nfd = unicodedata.normalize("NFD", path.name)
        for item in parent.iterdir():
            item_name_nfc = unicodedata.normalize("NFC", item.name)
            item_name_nfd = unicodedata.normalize("NFD", item.name)
            if item_name_nfc == target_name_nfc or item_name_nfd == target_name_nfd:
                return item
            if item_name_nfc == target_name_nfd or item_name_nfd == target_name_nfc:
                return item

    return None


def get_env_config() -> dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        "openrouter_model": os.environ.get(
            "OPENROUTER_MODEL", "google/gemini-2.5-flash"
        ),
        "openai_api_key": os.environ.get("OPENAI_API_KEY"),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL"),
        "openai_model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="translate_pdf",
            description="Translate a PDF document from one language to another. Supports bilingual (dual) and monolingual output modes. Uses AI-powered translation via OpenRouter or OpenAI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_file": {
                        "type": "string",
                        "description": "Absolute path to the input PDF file to translate.",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory where the translated PDF(s) will be saved. If not provided, uses the same directory as the input file.",
                    },
                    "lang_in": {
                        "type": "string",
                        "description": "Source language code (e.g., 'en' for English, 'zh' for Chinese). Default: 'en'",
                        "default": "en",
                    },
                    "lang_out": {
                        "type": "string",
                        "description": "Target language code (e.g., 'vi' for Vietnamese, 'zh' for Chinese, 'ja' for Japanese). Default: 'zh'",
                        "default": "zh",
                    },
                    "pages": {
                        "type": "string",
                        "description": "Pages to translate (e.g., '1,2,3', '1-5', '1,3-5,7'). If not set, translates all pages.",
                    },
                    "no_dual": {
                        "type": "boolean",
                        "description": "If true, do not output bilingual PDF (side-by-side original and translation). Default: false",
                        "default": False,
                    },
                    "no_mono": {
                        "type": "boolean",
                        "description": "If true, do not output monolingual translated PDF. Default: false",
                        "default": False,
                    },
                    "service": {
                        "type": "string",
                        "enum": ["openrouter", "openai"],
                        "description": "Translation service to use. Default: 'openrouter' (uses env vars for API key)",
                        "default": "openrouter",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use for translation. If not set, uses model from environment variable or default.",
                    },
                    "qps": {
                        "type": "integer",
                        "description": "Queries per second limit for translation API. Default: 4",
                        "default": 4,
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "Add watermark to output PDF. Default: true",
                        "default": True,
                    },
                },
                "required": ["input_file"],
            },
        ),
        Tool(
            name="get_translation_status",
            description="Get information about BabelDOC translation service configuration and supported languages.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    if name == "translate_pdf":
        return await translate_pdf(arguments)
    elif name == "get_translation_status":
        return await get_translation_status(arguments)
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )


async def get_translation_status(_arguments: dict[str, Any]) -> CallToolResult:
    """Get translation service status and configuration."""
    config = get_env_config()

    status = {
        "service": "BabelDOC MCP Server",
        "version": "1.0.0",
        "openrouter_configured": bool(config["openrouter_api_key"]),
        "openrouter_model": config["openrouter_model"],
        "openrouter_base_url": config["openrouter_base_url"],
        "openai_configured": bool(config["openai_api_key"]),
        "openai_model": config["openai_model"],
        "supported_languages": [
            "en (English)",
            "zh (Chinese)",
            "vi (Vietnamese)",
            "ja (Japanese)",
            "ko (Korean)",
            "es (Spanish)",
            "fr (French)",
            "de (German)",
            "pt (Portuguese)",
            "ru (Russian)",
            "ar (Arabic)",
            "th (Thai)",
            "id (Indonesian)",
        ],
    }

    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(status, indent=2),
            )
        ]
    )


async def translate_pdf(arguments: dict[str, Any]) -> CallToolResult:
    """Translate a PDF file."""
    input_file = arguments.get("input_file")
    if not input_file:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: input_file is required")]
        )

    # Resolve path with Unicode normalization support
    input_path = resolve_path_with_unicode_normalization(input_file)
    if input_path is None:
        return CallToolResult(
            content=[
                TextContent(type="text", text=f"Error: File not found: {input_file}")
            ]
        )

    if not input_path.suffix.lower() == ".pdf":
        return CallToolResult(
            content=[TextContent(type="text", text="Error: File must be a PDF")]
        )

    # Get configuration
    config = get_env_config()
    service = arguments.get("service", "openrouter")
    lang_in = arguments.get("lang_in", "en")
    lang_out = arguments.get("lang_out", "zh")
    pages = arguments.get("pages")
    no_dual = arguments.get("no_dual", False)
    no_mono = arguments.get("no_mono", False)
    qps = arguments.get("qps", 4)
    watermark = arguments.get("watermark", True)
    output_dir = arguments.get("output_dir") or str(input_path.parent)

    # Create translator based on service
    if service == "openrouter":
        api_key = config["openrouter_api_key"]
        if not api_key:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: OPENROUTER_API_KEY environment variable not set",
                    )
                ]
            )
        model = arguments.get("model") or config["openrouter_model"]
        base_url = config["openrouter_base_url"]
    elif service == "openai":
        api_key = config["openai_api_key"]
        if not api_key:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: OPENAI_API_KEY environment variable not set",
                    )
                ]
            )
        model = arguments.get("model") or config["openai_model"]
        base_url = config["openai_base_url"]
    else:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unknown service: {service}. Use 'openrouter' or 'openai'",
                )
            ]
        )

    try:
        # Initialize BabelDOC
        babeldoc.format.pdf.high_level.init()

        # Create translator
        translator = OpenAITranslator(
            lang_in=lang_in,
            lang_out=lang_out,
            model=model,
            base_url=base_url,
            api_key=api_key,
            ignore_cache=False,
            enable_json_mode_if_requested=False,
            send_dashscope_header=False,
            send_temperature=True,
        )

        # Set rate limiter
        set_translate_rate_limiter(qps)

        # Load document layout model
        from babeldoc.docvision.doclayout import DocLayoutModel

        doc_layout_model = DocLayoutModel.load_onnx()

        # Create output directory if needed
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Configure watermark mode
        watermark_mode = (
            WatermarkOutputMode.Watermarked
            if watermark
            else WatermarkOutputMode.NoWatermark
        )

        # Create translation config
        translation_config = TranslationConfig(
            input_file=str(input_path),
            font=None,
            pages=pages,
            output_dir=str(output_path),
            translator=translator,
            term_extraction_translator=translator,
            debug=False,
            lang_in=lang_in,
            lang_out=lang_out,
            no_dual=no_dual,
            no_mono=no_mono,
            qps=qps,
            formular_font_pattern=None,
            formular_char_pattern=None,
            split_short_lines=False,
            short_line_split_factor=0.8,
            doc_layout_model=doc_layout_model,
            skip_clean=False,
            dual_translate_first=False,
            disable_rich_text_translate=False,
            enhance_compatibility=False,
            use_alternating_pages_dual=False,
            report_interval=0.5,
            min_text_length=5,
            watermark_output_mode=watermark_mode,
            split_strategy=None,
            table_model=None,
            show_char_box=False,
            skip_scanned_detection=False,
            ocr_workaround=False,
            custom_system_prompt=None,
            working_dir=None,
            add_formula_placehold_hint=False,
            disable_same_text_fallback=False,
            glossaries=[],
            pool_max_workers=None,
            auto_extract_glossary=True,
            auto_enable_ocr_workaround=False,
            primary_font_family=None,
            only_include_translated_page=False,
            save_auto_extracted_glossary=False,
            enable_graphic_element_process=True,
            merge_alternating_line_numbers=True,
            skip_translation=False,
            skip_form_render=False,
            skip_curve_render=False,
            only_parse_generate_pdf=False,
            remove_non_formula_lines=False,
            non_formula_line_iou_threshold=0.9,
            figure_table_protection_threshold=0.9,
            skip_formula_offset_calculation=False,
            metadata_extra_data=None,
            term_pool_max_workers=None,
        )

        # Run translation
        result_info = None
        progress_info = []
        translation_error = None

        async for event in babeldoc.format.pdf.high_level.async_translate(
            translation_config
        ):
            if event["type"] == "progress_update":
                stage = event.get("stage", "unknown")
                current = event.get("stage_current", 0)
                total = event.get("stage_total", 100)
                progress_info.append(f"{stage}: {current}/{total}")
            elif event["type"] == "error":
                translation_error = event.get("error", "Unknown error")
            elif event["type"] == "finish":
                result_info = event.get("translate_result")

        if translation_error:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Translation error: {translation_error}",
                    )
                ]
            )

        # Build result message
        if result_info:
            result = {
                "status": "success",
                "input_file": str(input_path),
                "output_dir": str(output_path),
                "lang_in": lang_in,
                "lang_out": lang_out,
                "service": service,
                "model": model,
                "result": str(result_info),
                "token_usage": {
                    "total_tokens": translator.token_count.value,
                    "prompt_tokens": translator.prompt_token_count.value,
                    "completion_tokens": translator.completion_token_count.value,
                },
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Translation completed but no result information available",
                    )
                ]
            )

    except Exception as e:
        logger.exception("Translation failed")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Translation failed: {str(e)}")]
        )


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point for the MCP server script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
