import os
import re
import subprocess

docs_dir = r"C:\D\E\BioNeuronai\docs"

for filename in os.listdir(docs_dir):
    if not filename.endswith('.md'): continue
    filepath = os.path.join(docs_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Match ## 目錄 (or similar) followed by some text, ending at the next ## or ---
    match = re.search(r'^(##\s+.*?目錄.*?)\n(.*?)(?=\n##\s|\n---)', content, flags=re.MULTILINE | re.DOTALL)
    if not match:
        continue
        
    old_toc_content = match.group(2)
    # If it already has <!-- toc -->, we don't need to inject it again, but just to be safe we can replace it.
    
    new_content = content[:match.start(2)] + "\n<!-- toc -->\n\n" + content[match.end(2):]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Injecting TOC for {filename}...")
    subprocess.run(["npx", "markdown-toc", "-i", filepath, "--maxdepth", "3"], shell=True)
    print(f"Done processing {filename}")
