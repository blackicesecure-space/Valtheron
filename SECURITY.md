# Security Policy - Valtheron

## Overview

Valtheron is an agentic workspace framework that executes AI-driven tasks with access to file systems, code execution, and external APIs. Security is a critical concern given these capabilities.

## Supported Versions

| Version | Supported          | Notes                              |
| ------- | ------------------ | ---------------------------------- |
| 1.x.x   | :white_check_mark: | Current release, actively maintained |
| 0.x.x   | :x:                | Pre-release, no longer supported   |

## Security Model

### Agent Isolation

Agents operate within defined boundaries. Each agent has explicit tool access lists configured in their JSON definition. Agents cannot access tools not listed in their configuration. The `security.allowed_tools` setting in `workspace.json` provides an additional layer of control.

### Input Validation

All inputs are validated before processing when `security.validate_inputs` is enabled (default: true). This includes parameter type checking against JSON schemas, path traversal prevention for file operations, command injection prevention for bash execution, and size limits on inputs to prevent resource exhaustion.

### Output Sanitization

When `security.sanitize_outputs` is enabled (default: true), the system removes sensitive data patterns (API keys, credentials) from logs, sanitizes file paths in error messages, and filters internal system information from user-facing outputs.

### Credential Management

**Critical**: Never commit credentials to version control.

Store API keys in `.env` files (gitignored), use environment variables for sensitive configuration, rotate credentials regularly, and use the minimum required permissions for API keys.

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps.

### How to Report

Send an email to the repository maintainers with the subject line "SECURITY: [Brief Description]". Alternatively, use GitHub's private vulnerability reporting feature if available.

### What to Include

Please provide a clear description of the vulnerability, steps to reproduce the issue, potential impact assessment, and any suggested fixes if available.

### Response Timeline

You can expect an initial acknowledgment within 48 hours, a status update within 7 days, and a resolution timeline communicated within 14 days.

### What to Expect

If the vulnerability is accepted, we will work on a fix and coordinate disclosure. If declined, we will provide a detailed explanation. Credit will be given to reporters unless anonymity is requested.

## Security Best Practices for Users

### Configuration Security

Keep `security.validate_inputs` and `security.sanitize_outputs` enabled. Review agent tool access before deployment. Use `security.require_agent_auth` for production environments. Regularly audit `config/` files for sensitive data.

### File System Security

Restrict agent working directories. Use relative paths within the workspace. Avoid granting write access to system directories. Implement regular backups before automated operations.

### API Security

Use separate API keys for development and production. Implement rate limiting through the `rate_limits` configuration. Monitor API usage for anomalies. Revoke unused or compromised keys immediately.

### Code Execution Security

Review code before allowing agents to execute it. Use sandboxed environments for untrusted code. Set appropriate timeouts (`config.timeout_seconds`). Limit the maximum number of retries.

## Known Security Considerations

### Prompt Injection

Agents that process external content may be vulnerable to prompt injection. Validate and sanitize all external inputs. Use content filtering where appropriate. Monitor agent outputs for unexpected behavior.

### Path Traversal

The file operation tools include path validation to prevent directory traversal attacks. Ensure `validate_inputs` remains enabled. Be cautious with user-provided file paths.

### Command Injection

Bash tool usage requires careful input validation. Avoid constructing commands from user input. Use parameterized approaches where possible.

## Security Checklist for Deployment

Before deploying Valtheron, ensure that all API keys are stored in environment variables, `.env` files are in `.gitignore`, `security.validate_inputs` is `true`, `security.sanitize_outputs` is `true`, agent tool access is minimized to requirements, logging does not capture sensitive data, and file system access is appropriately restricted.

## Audit Logging

When `monitoring.enabled` is true, the system logs agent actions with timestamps, workflow execution details, error occurrences with context, and tool invocations.

Review logs regularly for unauthorized access attempts, unusual patterns of tool usage, failed authentication attempts, and unexpected error rates.

## Updates and Patches

Security updates will be released as patch versions (x.x.PATCH). Subscribe to repository notifications for security advisories. Apply security patches promptly.

## Contact

For security-related inquiries that are not vulnerability reports, please open a GitHub issue with the "security" label.

---

Last updated: 2026-01-22
