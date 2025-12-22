import markdown
import os

# Configuration
input_file = 'project_summary.md'
output_file = 'project_summary.html'

# CSS Style for professional report look
css_style = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f9f9f9;
    }
    .container {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 { border-bottom: 2px solid #eaeaea; padding-bottom: 0.5rem; color: #24292e; }
    h2 { border-bottom: 1px solid #eaeaea; padding-bottom: 0.3rem; margin-top: 2rem; color: #24292e; }
    h3 { margin-top: 1.5rem; color: #24292e; }
    code {
        background-color: #f6f8fa;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
        font-size: 85%;
    }
    pre {
        background-color: #f6f8fa;
        padding: 16px;
        border-radius: 6px;
        overflow: auto;
    }
    pre code {
        background-color: transparent;
        padding: 0;
    }
    blockquote {
        margin: 0;
        padding: 0 1em;
        color: #6a737d;
        border-left: 0.25em solid #dfe2e5;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
    }
    th, td {
        border: 1px solid #dfe2e5;
        padding: 6px 13px;
    }
    th {
        background-color: #f6f8fa;
        font-weight: 600;
    }
    tr:nth-child(2n) {
        background-color: #f8f8f8;
    }
    img {
        max-width: 100%;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        display: block;
        margin: 20px auto;
    }
    .alert {
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid transparent;
        border-radius: 4px;
    }
    .alert-important {
        color: #31708f;
        background-color: #d9edf7;
        border-color: #bce8f1;
    }
</style>
"""

# Read Markdown
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

# Convert to HTML
# extensions used:
# 'tables' for table support
# 'fenced_code' for code blocks
# 'toc' could be added but maybe overkill for this summary
html_content = markdown.markdown(text, extensions=['tables', 'fenced_code', 'nl2br'])

# Wrap in simple HTML structure
full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RocksDB RL Control Summary</title>
    {css_style}
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>
"""

# Write HTML
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"Successfully converted {input_file} to {output_file}")
