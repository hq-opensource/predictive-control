import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def add_citations(response):
    if not response or not response.candidates:
        return ""
        
    text = response.text
    metadata = response.candidates[0].grounding_metadata
    if not metadata or not metadata.grounding_supports:
        return text
        
    supports = metadata.grounding_supports
    chunks = metadata.grounding_chunks

    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    for support in sorted_supports:
        end_index = support.segment.end_index
        if support.grounding_chunk_indices:
            citation_links = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].web.uri
                    citation_links.append(f"[{i + 1}]({uri})")

            citation_string = " " + ", ".join(citation_links)
            text = text[:end_index] + citation_string + text[end_index:]

    return text

def analyze_compatibility(main_license, dep_license):
    if not dep_license or dep_license == "Unknown":
        return "Risk"
    
    permissive = ["MIT", "Apache", "BSD", "ISC", "Unlicense", "CC0", "LiLiQ-P"]
    copyleft = ["GPL", "AGPL", "LGPL", "MPL", "EPL", "EUPL"]
    
    dep_license_upper = dep_license.upper()
    
    for p in permissive:
        if p.upper() in dep_license_upper:
            return "Compatible"
    
    for c in copyleft:
        if c.upper() in dep_license_upper:
            return "Risk"
            
    return "Untreated"

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: GEMINI_API_KEY not set in .env file.")
        return

    client = genai.Client(api_key=api_key)
    
    local_analysis_file = Path("local_analysis.md")
    if not local_analysis_file.exists():
        print("Error: local_analysis.md not found. Run analyzer.py first.")
        return

    with open(local_analysis_file, "r", encoding="utf-8") as f:
        local_content = f.read()

    # Extract Main License
    main_lic_match = re.search(r"\*\*Main Repository License:\*\* (.*?)\n", local_content)
    main_license = main_lic_match.group(1) if main_lic_match else "Unknown"

    # Extract all libraries from the detailed list in local_analysis.md
    # We want to keep the ones that are already known and resolve the unknown ones.
    sections = re.findall(r"### (.*?)\n(.*?)(?=\n###|\Z)", local_content, re.DOTALL)
    
    final_data = {} # license -> list of packages
    unknown_packages = []

    for lic_name, pkg_list in sections:
        clean_lic = lic_name.strip()
        pkgs = [line.strip("- ").strip() for line in pkg_list.splitlines() if line.strip()]
        
        if clean_lic.lower() in ["unknown", "untreated"]:
            unknown_packages.extend(pkgs)
        else:
            if clean_lic not in final_data: final_data[clean_lic] = []
            final_data[clean_lic].extend(pkgs)

    if not unknown_packages:
        print("No unknown packages to resolve.")
        # Just copy local to final if nothing to do? No, let's still generate final_analysis.md
    else:
        print(f"Resolving {len(unknown_packages)} unknown packages...")

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        system_instruction="You are a legal and software licensing expert. Find the official license for the provided packages. Be concise. Reply with 'License: [Name]' followed by a brief explanation and citations."
    )

    references = []
    resolved_mapping = {}

    for pkg in unknown_packages:
        print(f"Searching for {pkg}...")
        prompt = f"What is the official license for the Python/Node.js package '{pkg}'? Provide the exact license name (e.g. MIT, Apache 2.0, BSD-3-Clause)."
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=config,
            )
            
            grounded_text = add_citations(response)
            references.append(f"## {pkg}\n{grounded_text}\n")
            
            # Simple heuristic to extract license name from response
            match = re.search(r"License:\s*([^\n\.]+)", response.text)
            if match:
                resolved_lic = match.group(1).strip()
            else:
                # Fallback: take the first line if it looks like a license
                resolved_lic = response.text.split('\n')[0].replace("License:", "").strip()
            
            if resolved_lic not in final_data: final_data[resolved_lic] = []
            final_data[resolved_lic].append(pkg)

        except Exception as e:
            print(f"Error resolving {pkg}: {e}")
            references.append(f"## {pkg}\nError: Could not resolve license.\n")
            if "Unknown" not in final_data: final_data["Unknown"] = []
            final_data["Unknown"].append(pkg)

    # Save details to references.md
    with open("references.md", "w", encoding="utf-8") as f:
        f.write("# LLM License Grounding References\n\n")
        f.write("This file contains the detailed search results and citations for previously unknown licenses.\n\n")
        f.write("\n".join(references))

    # Generate final_analysis.md
    with open("final_analysis.md", "w", encoding="utf-8") as f:
        f.write("# Final License Analysis Report\n\n")
        f.write(f"**Main Repository License:** {main_license}\n\n")
        f.write("## Summary\n\n")
        
        total_unique = sum(len(pkgs) for pkgs in final_data.values())
        f.write(f"- Total Unique Packages: {total_unique}\n")
        f.write(f"- Main License Compatibility: Permissive\n\n")
        
        f.write("## Compatibility Verdict\n\n")
        f.write("| License | Count | Status |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        for lic, pkgs in sorted(final_data.items()):
            status = analyze_compatibility(main_license, lic)
            display_lic = lic[:100]
            f.write(f"| {display_lic} | {len(pkgs)} | {status} |\n")
            
        f.write("\n## Complete Package Inventory\n\n")
        for lic, pkgs in sorted(final_data.items()):
            display_lic = lic[:100]
            f.write(f"### {display_lic}\n")
            # Determine type (naive check based on local_analysis.md could be improved, but we'll just list them)
            for pkg in sorted(pkgs):
                f.write(f"- {pkg}\n")
            f.write("\n")

    print("Success: Final report generated in final_analysis.md. Detailed references in references.md.")

if __name__ == "__main__":
    main()
