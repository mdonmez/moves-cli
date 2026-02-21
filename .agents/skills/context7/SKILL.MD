---
name: context7
description: Context7 is a set of tools for retrieving and using up-to-date documentation for libraries and frameworks. Use this skill whenever you need to work with external libraries, APIs, or frameworks to ensure your code is based on the latest information rather than outdated training data.
---

Always use Context7 MCP tools before planning or implementing code that involves external libraries or frameworks:

1. Use `resolve-library-id` to get the correct library identifier
2. Use `get-library-docs` to pull current documentation
3. Base all code suggestions on the retrieved documentation, not training data

This applies to any library usage, API integration, or framework-specific patterns.