import os
import json

projects_dir = r"C:\Users\Saboor\.gemini\config\projects"
found = []

if os.path.exists(projects_dir):
    for filename in os.listdir(projects_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(projects_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # Convert to string to search for ai_detection
                    content_str = json.dumps(content)
                    if "ai_detection" in content_str or "ai-detection" in content_str:
                        found.append((filename, content))
            except Exception as e:
                print(f"Error reading {filename}: {e}")
else:
    print(f"Projects directory not found at {projects_dir}")

print(f"Found {len(found)} matching project configurations:")
for name, data in found:
    print(f"\n--- {name} ---")
    print(json.dumps(data, indent=2))
