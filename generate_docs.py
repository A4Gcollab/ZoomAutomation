
import base64
import os

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VONG Master Documentation</title>
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; color: #1a1a1a; line-height: 1.6; }
        h1, h2, h3 { color: #111; margin-top: 1.5em; }
        h1 { font-size: 2.5em; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }
        h2 { font-size: 1.8em; border-bottom: 1px solid #eaeaea; padding-bottom: 8px; }
        code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-family: 'Monaco', 'Consolas', monospace; font-size: 0.9em; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 8px; overflow-x: auto; }
        pre code { background: none; padding: 0; }
        blockquote { border-left: 4px solid #0070f3; margin: 0; padding-left: 20px; background: #f0f7ff; padding: 10px 20px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f9f9f9; font-weight: 600; }
        .mermaid { text-align: center; margin: 30px 0; }
        .print-btn { position: fixed; top: 20px; right: 20px; padding: 10px 20px; background: #0070f3; color: white; text-decoration: none; border-radius: 5px; font-weight: 600; cursor: pointer; border: none; }
        @media print { .print-btn { display: none; } body { padding: 0; } }
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Save as PDF</button>
    <div id="content"></div>
    
    <!-- Hidden element to store Base64 markdown -->
    <div id="markdown-source" style="display:none;">B64_CONTENT_HERE</div>

    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        
        mermaid.initialize({ startOnLoad: false, theme: 'neutral' });

        // Decode Base64 Content
        const b64 = document.getElementById('markdown-source').textContent;
        const rawMarkdown = new TextDecoder().decode(Uint8Array.from(atob(b64), c => c.charCodeAt(0)));

        // Configure Marked to identify mermaid blocks
        const renderer = new marked.Renderer();
        const oldCode = renderer.code;
        renderer.code = function(code, language) {
            if (language === 'mermaid') {
                return '<div class="mermaid">' + code + '</div>';
            }
            return oldCode.call(this, code, language);
        };

        // Render Markdown to HTML
        document.getElementById('content').innerHTML = marked.parse(rawMarkdown, { renderer: renderer });
        
        // Render Mermaid Diagrams
        setTimeout(async () => {
            await mermaid.run({
                querySelector: '.mermaid'
            });
        }, 100);
    </script>
</body>
</html>
"""

def generate_html(md_path, html_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Base64 encode to safely embed in HTML without string escaping issues
    b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    final_html = TEMPLATE.replace("B64_CONTENT_HERE", b64_content)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Generated {html_path}")

if __name__ == "__main__":
    input_path = os.path.join(os.path.dirname(__file__), 'docs', 'MASTER_DOCUMENTATION.md')
    output_path = os.path.join(os.path.dirname(__file__), 'docs', 'index.html')
    
    # Ensure docs directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    generate_html(input_path, output_path)
