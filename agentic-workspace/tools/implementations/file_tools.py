"""
File operation tools for the agentic workspace.
Provides read, write, edit, glob, and grep functionality.
"""
import os
import re
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any
import difflib

from .base import BaseTool, ToolParameter, ToolResult, register_tool


class ReadFileTool(BaseTool):
    """Read contents of a file."""
    
    @property
    def name(self) -> str:
        return "read"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file at the specified path"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to read"
            ),
            ToolParameter(
                name="encoding",
                param_type="string",
                description="File encoding",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="start_line",
                param_type="integer",
                description="Starting line number (1-indexed)",
                required=False
            ),
            ToolParameter(
                name="end_line",
                param_type="integer",
                description="Ending line number (inclusive)",
                required=False
            )
        ]
    
    def execute(self, file_path: str, encoding: str = "utf-8",
                start_line: Optional[int] = None, end_line: Optional[int] = None) -> ToolResult:
        path = Path(file_path)
        
        if not path.exists():
            return ToolResult.failure(f"File not found: {file_path}", "FileNotFoundError")
        
        if not path.is_file():
            return ToolResult.failure(f"Not a file: {file_path}", "IsADirectoryError")
        
        try:
            with open(path, "r", encoding=encoding) as f:
                if start_line is not None or end_line is not None:
                    lines = f.readlines()
                    start_idx = (start_line - 1) if start_line else 0
                    end_idx = end_line if end_line else len(lines)
                    content = "".join(lines[start_idx:end_idx])
                else:
                    content = f.read()
            
            return ToolResult.success(
                data={
                    "content": content,
                    "path": str(path.absolute()),
                    "size_bytes": path.stat().st_size,
                    "lines": content.count("\n") + (1 if content and not content.endswith("\n") else 0)
                },
                metadata={"encoding": encoding}
            )
        except UnicodeDecodeError as e:
            return ToolResult.failure(f"Encoding error: {e}", "UnicodeDecodeError")
        except PermissionError:
            return ToolResult.failure(f"Permission denied: {file_path}", "PermissionError")


class WriteFileTool(BaseTool):
    """Write content to a file."""
    
    @property
    def name(self) -> str:
        return "write"
    
    @property
    def description(self) -> str:
        return "Write content to a file, creating it if it doesn't exist"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to write"
            ),
            ToolParameter(
                name="content",
                param_type="string",
                description="Content to write to the file"
            ),
            ToolParameter(
                name="mode",
                param_type="string",
                description="Write mode: 'overwrite' or 'append'",
                required=False,
                default="overwrite",
                enum_values=["overwrite", "append"]
            ),
            ToolParameter(
                name="create_dirs",
                param_type="boolean",
                description="Create parent directories if they don't exist",
                required=False,
                default=True
            ),
            ToolParameter(
                name="encoding",
                param_type="string",
                description="File encoding",
                required=False,
                default="utf-8"
            )
        ]
    
    def execute(self, file_path: str, content: str, mode: str = "overwrite",
                create_dirs: bool = True, encoding: str = "utf-8") -> ToolResult:
        path = Path(file_path)
        
        if create_dirs and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        write_mode = "w" if mode == "overwrite" else "a"
        
        try:
            with open(path, write_mode, encoding=encoding) as f:
                f.write(content)
            
            return ToolResult.success(
                data={
                    "path": str(path.absolute()),
                    "bytes_written": len(content.encode(encoding)),
                    "mode": mode
                }
            )
        except PermissionError:
            return ToolResult.failure(f"Permission denied: {file_path}", "PermissionError")


class EditFileTool(BaseTool):
    """Edit a file using string replacement."""
    
    @property
    def name(self) -> str:
        return "edit"
    
    @property
    def description(self) -> str:
        return "Edit a file by replacing a unique string with new content"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to edit"
            ),
            ToolParameter(
                name="old_string",
                param_type="string",
                description="String to find and replace (must be unique in file)"
            ),
            ToolParameter(
                name="new_string",
                param_type="string",
                description="Replacement string"
            ),
            ToolParameter(
                name="encoding",
                param_type="string",
                description="File encoding",
                required=False,
                default="utf-8"
            )
        ]
    
    def execute(self, file_path: str, old_string: str, new_string: str,
                encoding: str = "utf-8") -> ToolResult:
        path = Path(file_path)
        
        if not path.exists():
            return ToolResult.failure(f"File not found: {file_path}", "FileNotFoundError")
        
        try:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            
            count = content.count(old_string)
            
            if count == 0:
                return ToolResult.failure(
                    f"String not found in file: {old_string[:50]}...",
                    "StringNotFoundError"
                )
            
            if count > 1:
                return ToolResult.failure(
                    f"String appears {count} times in file (must be unique)",
                    "AmbiguousMatchError"
                )
            
            new_content = content.replace(old_string, new_string)
            
            with open(path, "w", encoding=encoding) as f:
                f.write(new_content)
            
            # Generate diff
            diff = list(difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}"
            ))
            
            return ToolResult.success(
                data={
                    "path": str(path.absolute()),
                    "diff": "".join(diff),
                    "characters_removed": len(old_string),
                    "characters_added": len(new_string)
                }
            )
        except PermissionError:
            return ToolResult.failure(f"Permission denied: {file_path}", "PermissionError")


class GlobTool(BaseTool):
    """Find files matching a pattern."""
    
    @property
    def name(self) -> str:
        return "glob"
    
    @property
    def description(self) -> str:
        return "Find files matching a glob pattern"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                param_type="string",
                description="Glob pattern to match (e.g., '**/*.py')"
            ),
            ToolParameter(
                name="base_path",
                param_type="string",
                description="Base directory to search from",
                required=False,
                default="."
            ),
            ToolParameter(
                name="include_hidden",
                param_type="boolean",
                description="Include hidden files/directories",
                required=False,
                default=False
            ),
            ToolParameter(
                name="max_results",
                param_type="integer",
                description="Maximum number of results to return",
                required=False,
                default=1000
            )
        ]
    
    def execute(self, pattern: str, base_path: str = ".",
                include_hidden: bool = False, max_results: int = 1000) -> ToolResult:
        base = Path(base_path)
        
        if not base.exists():
            return ToolResult.failure(f"Base path not found: {base_path}", "FileNotFoundError")
        
        try:
            matches = []
            for match in base.glob(pattern):
                if not include_hidden:
                    # Skip hidden files/directories
                    parts = match.relative_to(base).parts
                    if any(part.startswith(".") for part in parts):
                        continue
                
                matches.append({
                    "path": str(match),
                    "is_file": match.is_file(),
                    "is_dir": match.is_dir(),
                    "size": match.stat().st_size if match.is_file() else None
                })
                
                if len(matches) >= max_results:
                    break
            
            return ToolResult.success(
                data={
                    "matches": matches,
                    "count": len(matches),
                    "truncated": len(matches) >= max_results
                },
                metadata={"pattern": pattern, "base_path": str(base.absolute())}
            )
        except PermissionError as e:
            return ToolResult.failure(f"Permission denied: {e}", "PermissionError")


class GrepTool(BaseTool):
    """Search for patterns in files."""
    
    @property
    def name(self) -> str:
        return "grep"
    
    @property
    def description(self) -> str:
        return "Search for a pattern in files"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                param_type="string",
                description="Regular expression pattern to search for"
            ),
            ToolParameter(
                name="path",
                param_type="string",
                description="File or directory to search"
            ),
            ToolParameter(
                name="file_pattern",
                param_type="string",
                description="Glob pattern for files to search (when path is directory)",
                required=False,
                default="*"
            ),
            ToolParameter(
                name="case_sensitive",
                param_type="boolean",
                description="Case-sensitive search",
                required=False,
                default=True
            ),
            ToolParameter(
                name="context_lines",
                param_type="integer",
                description="Number of context lines to include",
                required=False,
                default=0
            ),
            ToolParameter(
                name="max_matches",
                param_type="integer",
                description="Maximum number of matches to return",
                required=False,
                default=100
            )
        ]
    
    def execute(self, pattern: str, path: str, file_pattern: str = "*",
                case_sensitive: bool = True, context_lines: int = 0,
                max_matches: int = 100) -> ToolResult:
        target = Path(path)
        
        if not target.exists():
            return ToolResult.failure(f"Path not found: {path}", "FileNotFoundError")
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult.failure(f"Invalid regex: {e}", "RegexError")
        
        matches = []
        files_searched = 0
        
        def search_file(file_path: Path):
            nonlocal files_searched
            files_searched += 1
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except (PermissionError, IsADirectoryError):
                return
            
            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    match_data = {
                        "file": str(file_path),
                        "line_number": line_num,
                        "line": line.rstrip("\n"),
                        "context_before": [],
                        "context_after": []
                    }
                    
                    if context_lines > 0:
                        start = max(0, line_num - 1 - context_lines)
                        end = min(len(lines), line_num + context_lines)
                        match_data["context_before"] = [l.rstrip("\n") for l in lines[start:line_num-1]]
                        match_data["context_after"] = [l.rstrip("\n") for l in lines[line_num:end]]
                    
                    matches.append(match_data)
                    
                    if len(matches) >= max_matches:
                        return
        
        if target.is_file():
            search_file(target)
        else:
            for file_path in target.rglob(file_pattern):
                if file_path.is_file():
                    search_file(file_path)
                    if len(matches) >= max_matches:
                        break
        
        return ToolResult.success(
            data={
                "matches": matches,
                "total_matches": len(matches),
                "files_searched": files_searched,
                "truncated": len(matches) >= max_matches
            },
            metadata={"pattern": pattern, "path": str(target.absolute())}
        )


# Register all file tools
register_tool(ReadFileTool())
register_tool(WriteFileTool())
register_tool(EditFileTool())
register_tool(GlobTool())
register_tool(GrepTool())
