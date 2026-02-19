import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: GEMINI_API_KEY not set in .env file.")
        return

    client = genai.Client(api_key=api_key)
    
    final_analysis_file = Path("final_analysis.md")
    if not final_analysis_file.exists():
        print("Error: final_analysis.md not found. Ensure you've run the first step and cleaned the file.")
        return

    with open(final_analysis_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the Complete Package Inventory section
    inventory_match = re.search(r"## Complete Package Inventory(.*)", content, re.DOTALL)
    if not inventory_match:
        print("Error: '## Complete Package Inventory' section not found in final_analysis.md")
        return

    inventory_text = inventory_match.group(1)
    
    # Extract unique packages from the inventory
    package_lines = re.findall(r"^- (.*)", inventory_text, re.MULTILINE)
    unique_packages = sorted(list(set([p.split('(')[0].strip() for p in package_lines])))

    print(f"Found {len(unique_packages)} unique packages to link.")

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        system_instruction="Find the official GitHub repository URL for the software package. Return ONLY the URL."
    )

    links_mapping = {}
    for pkg in unique_packages:
        print(f"Searching GitHub link for {pkg}...")
        prompt = f"What is the official GitHub repository URL for the package '{pkg}'?"
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=config,
            )
            # Find a URL in the response
            url_match = re.search(r'https?://github\.com/[^\s\)\],`]+', response.text)
            if url_match:
                url = url_match.group(0).rstrip('/')
                # Strip trailing punctuation common in LLM responses
                url = url.rstrip('.:;`"\'')
                links_mapping[pkg] = url
            else:
                links_mapping[pkg] = "Link not found"
        except Exception as e:
            print(f"Error finding link for {pkg}: {e}")
            links_mapping[pkg] = "Error"

    # Now update the content with links
    def add_link(match):
        full_line = match.group(0)
        pkg_part = match.group(1)
        pkg_name = pkg_part.split('(')[0].strip()
        link = links_mapping.get(pkg_name)
        if link and link.startswith("http"):
            return f"- [{pkg_part}]({link})"
        return full_line

    # Apply replacement only to the inventory section
    updated_inventory = re.sub(r"^- (.*)", add_link, inventory_text, flags=re.MULTILINE)
    
    final_content = content[:inventory_match.start(1)] + updated_inventory

    with open("final_analysis_with_links.md", "w", encoding="utf-8") as f:
        f.write(final_content)

    print("Success: Links added. Final report: final_analysis_with_links.md")

if __name__ == "__main__":
    main()
