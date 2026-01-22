"""
File Operations Tool Implementation.
Provides secure file reading, writing, and manipulation capabilities.
"""
import os
import re
import shutil
import hashlib
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_tool import (
    BaseTool, ToolResult, ToolStatus, ToolParameter, ToolRegistry
)


class PathValidator:
    """Validates and sanitizes file paths for security."""

    def __init__(self, allowed_roots: Optional[List[str]] = None):
        self.allowed_roots = [Path(r).resolve() for r in (allowed_roots or ["."])]

    def validate(self, path: str) -> tuple[bool, Optional[str], Optional[Path]]:
        """
        Validate a path is safe to access.
        
        Returns:
            Tuple of (is_valid, error_message, resolved_path)
        """
        try:
            # Resolve to absolute path
            resolved = Path(path).resolve()

            # Check for path traversal attempts
            if ".." in str(path):
                # Double-check resolved path is within allowed roots
                if not any(self._is_subpath(resolved, root) for root in self.allowed_roots):
                    return False, "Path traversal detected", None

            # Check path is within allowed roots
            if not any(self._is_subpath(resolved, root) for root in self.allowed_roots):
                return False, f"Path outside allowed directories: {resolved}", None

            return True, None, resolved

        except Exception as e:
            return False, f"Invalid path: {e}", None

    def _is_subpath(self, path: Path, root: Path) -> bool:
        """Check if path is a subpath of root."""
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False


@ToolRegistry.register
class FileReadTool(BaseTool):
    """Reads file contents with encoding detection and size limits."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_size_bytes = self.config.get("max_size_bytes", 10 * 1024 * 1024)  # 10MB
        self.allowed_roots = self.config.get("allowed_roots", ["."])
        self.validator = PathValidator(self.allowed_roots)

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read the contents of a file with encoding detection"

    @classmethod
    def get_parameters(cls) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to read",
                required=True
            ),
            ToolParameter(
                name="encoding",
                param_type="string",
                description="File encoding (auto-detected if not specified)",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="lines",
                param_type="object",
                description="Read specific line range: {start: int, end: int}",
                required=False
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path")
        encoding = kwargs.get("encoding", "utf-8")
        lines_range = kwargs.get("lines")

        # Validate path
        is_valid, error, resolved_path = self.validator.validate(file_path)
        if not is_valid:
            return ToolResult(status=ToolStatus.PERMISSION_DENIED, error=error)

        if not resolved_path.exists():
            return ToolResult(status=ToolStatus.ERROR, error=f"File not found: {file_path}")

        if not resolved_path.is_file():
            return ToolResult(status=ToolStatus.ERROR, error=f"Not a file: {file_path}")

        # Check file size
        file_size = resolved_path.stat().st_size
        if file_size > self.max_size_bytes:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"File too large: {file_size} bytes (max: {self.max_size_bytes})"
            )

        try:
            # Try to read with specified encoding, fallback to others
            content = None
            encodings = [encoding, "utf-8", "latin-1", "cp1252"]
            
            for enc in encodings:
                try:
                    content = resolved_path.read_text(encoding=enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                # Read as binary if all encodings fail
                content = resolved_path.read_bytes().decode("utf-8", errors="replace")

            # Apply line range if specified
            if lines_range:
                lines = content.split("\n")
                start = lines_range.get("start", 1) - 1
                end = lines_range.get("end", len(lines))
                content = "\n".join(lines[start:end])

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "content": content,
                    "path": str(resolved_path),
                    "size_bytes": file_size,
                    "encoding": encoding,
                    "line_count": content.count("\n") + 1
                }
            )

        except Exception as e:
            return ToolResult(status=ToolStatus.ERROR, error=f"Read error: {e}")


@ToolRegistry.register
class FileWriteTool(BaseTool):
    """Writes content to files with backup and atomic write options."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.allowed_roots = self.config.get("allowed_roots", ["."])
        self.create_backup = self.config.get("create_backup", True)
        self.validator = PathValidator(self.allowed_roots)

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "Write content to a file with optional backup"

    @classmethod
    def get_parameters(cls) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to write",
                required=True
            ),
            ToolParameter(
                name="content",
                param_type="string",
                description="Content to write to the file",
                required=True
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
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        mode = kwargs.get("mode", "overwrite")
        create_dirs = kwargs.get("create_dirs", True)

        # Validate path
        is_valid, error, resolved_path = self.validator.validate(file_path)
        if not is_valid:
            return ToolResult(status=ToolStatus.PERMISSION_DENIED, error=error)

        try:
            # Create parent directories if needed
            if create_dirs:
                resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file exists
            backup_path = None
            if self.create_backup and resolved_path.exists():
                backup_path = resolved_path.with_suffix(
                    resolved_path.suffix + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                shutil.copy2(resolved_path, backup_path)

            # Write content
            write_mode = "w" if mode == "overwrite" else "a"
            with open(resolved_path, write_mode, encoding="utf-8") as f:
                f.write(content)

            # Calculate hash for verification
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "path": str(resolved_path),
                    "bytes_written": len(content.encode()),
                    "mode": mode,
                    "content_hash": content_hash,
                    "backup_path": str(backup_path) if backup_path else None
                }
            )

        except PermissionError:
            return ToolResult(status=ToolStatus.PERMISSION_DENIED, error=f"Permission denied: {file_path}")
        except Exception as e:
            return ToolResult(status=ToolStatus.ERROR, error=f"Write error: {e}")


@ToolRegistry.register  
class FileSearchTool(BaseTool):
    """Searches for files matching patterns and content."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.allowed_roots = self.config.get("allowed_roots", ["."])
        self.max_results = self.config.get("max_results", 100)
        self.validator = PathValidator(self.allowed_roots)

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return "Search for files matching glob patterns"

    @classmethod
    def get_parameters(cls) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                param_type="string",
                description="Glob pattern to match (e.g., '**/*.py')",
                required=True
            ),
            ToolParameter(
                name="directory",
                param_type="string",
                description="Starting directory for search",
                required=False,
                default="."
            ),
            ToolParameter(
                name="exclude",
                param_type="array",
                description="Patterns to exclude",
                required=False
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        pattern = kwargs.get("pattern")
        directory = kwargs.get("directory", ".")
        exclude = kwargs.get("exclude", [])

        # Validate directory
        is_valid, error, resolved_dir = self.validator.validate(directory)
        if not is_valid:
            return ToolResult(status=ToolStatus.PERMISSION_DENIED, error=error)

        if not resolved_dir.is_dir():
            return ToolResult(status=ToolStatus.ERROR, error=f"Not a directory: {directory}")

        try:
            # Find matching files
            matches = []
            for path in resolved_dir.glob(pattern):
                # Skip excluded patterns
                skip = False
                for excl in exclude:
                    if fnmatch.fnmatch(str(path), excl):
                        skip = True
                        break
                
                if skip:
                    continue

                # Validate each match is within allowed roots
                is_valid, _, _ = self.validator.validate(str(path))
                if not is_valid:
                    continue

                matches.append({
                    "path": str(path),
                    "name": path.name,
                    "is_file": path.is_file(),
                    "size": path.stat().st_size if path.is_file() else None
                })

                if len(matches) >= self.max_results:
                    break

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "matches": matches,
                    "count": len(matches),
                    "pattern": pattern,
                    "directory": str(resolved_dir),
                    "truncated": len(matches) >= self.max_results
                }
            )

        except Exception as e:
            return ToolResult(status=ToolStatus.ERROR, error=f"Search error: {e}")


@ToolRegistry.register
class GrepTool(BaseTool):
    """Searches file contents for patterns."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.allowed_roots = self.config.get("allowed_roots", ["."])
        self.max_matches = self.config.get("max_matches", 500)
        self.validator = PathValidator(self.allowed_roots)

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "Search for patterns in file contents"

    @classmethod
    def get_parameters(cls) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                param_type="string",
                description="Search pattern (regex supported)",
                required=True
            ),
            ToolParameter(
                name="path",
                param_type="string",
                description="File or directory to search",
                required=True
            ),
            ToolParameter(
                name="file_pattern",
                param_type="string",
                description="Glob pattern for files to search (e.g., '*.py')",
                required=False,
                default="*"
            ),
            ToolParameter(
                name="case_sensitive",
                param_type="boolean",
                description="Whether search is case-sensitive",
                required=False,
                default=True
            ),
            ToolParameter(
                name="context_lines",
                param_type="integer",
                description="Number of context lines around matches",
                required=False,
                default=0
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        pattern = kwargs.get("pattern")
        path = kwargs.get("path")
        file_pattern = kwargs.get("file_pattern", "*")
        case_sensitive = kwargs.get("case_sensitive", True)
        context_lines = kwargs.get("context_lines", 0)

        # Validate path
        is_valid, error, resolved_path = self.validator.validate(path)
        if not is_valid:
            return ToolResult(status=ToolStatus.PERMISSION_DENIED, error=error)

        if not resolved_path.exists():
            return ToolResult(status=ToolStatus.ERROR, error=f"Path not found: {path}")

        try:
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult(status=ToolStatus.INVALID_INPUT, error=f"Invalid regex: {e}")

        matches = []
        files_searched = 0

        try:
            # Get files to search
            if resolved_path.is_file():
                files = [resolved_path]
            else:
                files = list(resolved_path.glob(f"**/{file_pattern}"))

            for file_path in files:
                if not file_path.is_file():
                    continue
                    
                files_searched += 1
                
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.split("\n")
                    
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            # Get context
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            context = lines[start:end] if context_lines > 0 else None
                            
                            matches.append({
                                "file": str(file_path),
                                "line_number": i + 1,
                                "line": line.strip(),
                                "context": context
                            })
                            
                            if len(matches) >= self.max_matches:
                                break
                                
                except Exception:
                    continue  # Skip files that can't be read
                    
                if len(matches) >= self.max_matches:
                    break

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "matches": matches,
                    "count": len(matches),
                    "files_searched": files_searched,
                    "pattern": pattern,
                    "truncated": len(matches) >= self.max_matches
                }
            )

        except Exception as e:
            return ToolResult(status=ToolStatus.ERROR, error=f"Search error: {e}")


@ToolRegistry.register
class FileEditTool(BaseTool):
    """Edits files with search and replace operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.allowed_roots = self.config.get("allowed_roots", ["."])
        self.create_backup = self.config.get("create_backup", True)
        self.validator = PathValidator(self.allowed_roots)

    @property
    def name(self) -> str:
        return "edit"

    @property
    def description(self) -> str:
        return "Edit file contents with search and replace"

    @classmethod
    def get_parameters(cls) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to edit",
                required=True
            ),
            ToolParameter(
                name="old_text",
                param_type="string",
                description="Text to find (exact match)",
                required=True
            ),
            ToolParameter(
                name="new_text",
                param_type="string",
                description="Text to replace with",
                required=True
            ),
            ToolParameter(
                name="occurrence",
                param_type="string",
                description="Which occurrence to replace: 'first', 'last', or 'all'",
                required=False,
                default="first",
                enum_values=["first", "last", "all"]
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path")
        old_text = kwargs.get("old_text")
        new_text = kwargs.get("new_text")
        occurrence = kwargs.get("occurrence", "first")

        # Validate path
        is_valid, error, resolved_path = self.validator.validate(file_path)
        if not is_valid:
            return ToolResult(status=ToolStatus.PERMISSION_DENIED, error=error)

        if not resolved_path.exists():
            return ToolResult(status=ToolStatus.ERROR, error=f"File not found: {file_path}")

        try:
            content = resolved_path.read_text(encoding="utf-8")
            
            # Check if old_text exists
            count = content.count(old_text)
            if count == 0:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="Text to replace not found in file"
                )

            # Create backup
            backup_path = None
            if self.create_backup:
                backup_path = resolved_path.with_suffix(
                    resolved_path.suffix + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                shutil.copy2(resolved_path, backup_path)

            # Perform replacement
            if occurrence == "all":
                new_content = content.replace(old_text, new_text)
                replacements = count
            elif occurrence == "first":
                new_content = content.replace(old_text, new_text, 1)
                replacements = 1
            else:  # last
                # Replace last occurrence
                idx = content.rfind(old_text)
                new_content = content[:idx] + new_text + content[idx + len(old_text):]
                replacements = 1

            # Write updated content
            resolved_path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "path": str(resolved_path),
                    "replacements_made": replacements,
                    "occurrences_found": count,
                    "backup_path": str(backup_path) if backup_path else None
                }
            )

        except Exception as e:
            return ToolResult(status=ToolStatus.ERROR, error=f"Edit error: {e}")
