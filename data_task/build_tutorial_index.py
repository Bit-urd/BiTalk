import os
import json
import re
import glob
import nbformat
from nbconvert import MarkdownExporter
from datetime import datetime
import yaml
import shutil

from config import config, logger
from utils import (
    retry_on_failure, ensure_directory, save_json, save_markdown,
    clean_filename, truncate_text
)

@retry_on_failure(max_retries=config.scraping.max_retries)
def scan_tutorials(tutorials_dir):
    """
    Scan the tutorials directory to find all tutorial files
    """
    # Find all markdown files
    md_files = glob.glob(os.path.join(tutorials_dir, "**/*.md"), recursive=True)
    
    # Find all Jupyter notebook files
    ipynb_files = glob.glob(os.path.join(tutorials_dir, "**/*.ipynb"), recursive=True)
    
    return {
        "markdown": md_files,
        "jupyter": ipynb_files
    }

def extract_metadata_from_markdown(file_path):
    """
    Extract metadata from markdown file's frontmatter
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML frontmatter
    frontmatter_match = re.search(r'^---\s*(.*?)\s*---', content, re.DOTALL)
    
    if frontmatter_match:
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            
            # Extract title, date, tags, etc.
            metadata = {
                "title": frontmatter.get("title", os.path.basename(file_path)),
                "date": frontmatter.get("date", ""),
                "tags": frontmatter.get("tags", []),
                "categories": frontmatter.get("categories", []),
                "description": frontmatter.get("description", ""),
                "path": file_path,
                "type": "markdown"
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error parsing frontmatter in {file_path}: {e}")
    
    # If no frontmatter or error, return basic metadata
    return {
        "title": os.path.basename(file_path).replace(".md", "").replace("-", " ").title(),
        "date": "",
        "tags": [],
        "categories": [],
        "description": "",
        "path": file_path,
        "type": "markdown"
    }

def extract_metadata_from_jupyter(file_path):
    """
    Extract metadata from Jupyter notebook
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        
        # Try to extract title from first cell if it's markdown
        title = os.path.basename(file_path).replace(".ipynb", "").replace("_", " ").title()
        description = ""
        
        if notebook.cells and notebook.cells[0].cell_type == "markdown":
            first_cell = notebook.cells[0].source
            
            # Check for title in first cell
            title_match = re.search(r'^#\s+(.+)$', first_cell, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
            
            # Try to extract description
            lines = first_cell.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    # Look for text after the title
                    if i+1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith('#'):
                        description = lines[i+1].strip()
                        break
        
        # Extract tags from notebook metadata if available
        tags = []
        if hasattr(notebook.metadata, 'tags'):
            tags = notebook.metadata.tags
        
        return {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": tags,
            "categories": [],
            "description": description,
            "path": file_path,
            "type": "jupyter"
        }
    except Exception as e:
        logger.error(f"Error processing Jupyter notebook {file_path}: {e}")
        return {
            "title": os.path.basename(file_path).replace(".ipynb", "").replace("_", " ").title(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": [],
            "categories": [],
            "description": "",
            "path": file_path,
            "type": "jupyter"
        }

def convert_jupyter_to_markdown(notebook_path, output_dir):
    """
    Convert Jupyter notebook to Hugo-compatible markdown
    """
    try:
        # Read the notebook
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        
        # Configure the exporter
        exporter = MarkdownExporter()
        
        # Convert to markdown
        markdown, resources = exporter.from_notebook_node(notebook)
        
        # Extract metadata
        metadata = extract_metadata_from_jupyter(notebook_path)
        
        # Create Hugo frontmatter
        frontmatter = {
            "title": metadata["title"],
            "date": metadata["date"],
            "draft": False,
            "tags": metadata["tags"],
            "categories": metadata["categories"],
            "description": metadata["description"]
        }
        
        # Convert frontmatter to YAML
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False)
        
        # Add frontmatter to markdown
        hugo_markdown = f"---\n{frontmatter_yaml}---\n\n{markdown}"
        
        # Determine output path
        base_name = os.path.basename(notebook_path).replace(".ipynb", ".md")
        output_path = os.path.join(output_dir, base_name)
        
        # Save images if any
        if resources and 'outputs' in resources:
            img_dir = os.path.join(output_dir, "images", base_name.replace(".md", ""))
            os.makedirs(img_dir, exist_ok=True)
            
            for img_name, img_data in resources['outputs'].items():
                img_path = os.path.join(img_dir, img_name)
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                # Update image paths in markdown
                hugo_markdown = hugo_markdown.replace(f"![{img_name}]({img_name})", 
                                                     f"![{img_name}](images/{base_name.replace('.md', '')}/{img_name})")
        
        # Save the markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(hugo_markdown)
        
        logger.info(f"Converted {notebook_path} to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error converting notebook {notebook_path}: {e}")
        return None

def categorize_tutorials(tutorials):
    """
    Categorize tutorials by tags and categories
    """
    categories = {}
    tags = {}
    
    for tutorial in tutorials:
        # Categorize by category
        for category in tutorial.get("categories", []):
            if category not in categories:
                categories[category] = []
            categories[category].append(tutorial)
        
        # Categorize by tag
        for tag in tutorial.get("tags", []):
            if tag not in tags:
                tags[tag] = []
            tags[tag].append(tutorial)
    
    return {
        "by_category": categories,
        "by_tag": tags
    }

def generate_index_page(tutorials, output_path):
    """
    Generate an index page for all tutorials
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create frontmatter
    frontmatter = {
        "title": "Tutorials Index",
        "date": now,
        "draft": False,
        "description": "Index of all tutorials"
    }
    
    # Convert frontmatter to YAML
    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False)
    
    # Start building the markdown content
    markdown = f"""---
{frontmatter_yaml}---

# Tutorial Index

*Last updated: {now}*

Welcome to our comprehensive tutorial collection. Browse by category or explore the full list below.

## Categories

"""
    
    # Add categories section
    categorized = categorize_tutorials(tutorials)
    
    for category, category_tutorials in sorted(categorized["by_category"].items()):
        markdown += f"### {category.title()}\n\n"
        
        for tutorial in sorted(category_tutorials, key=lambda x: x.get("title", "")):
            relative_path = os.path.relpath(tutorial["path"], os.path.dirname(output_path))
            relative_path = relative_path.replace(".md", "/").replace("\\", "/")
            
            markdown += f"- [{tutorial['title']}]({relative_path})"
            
            if tutorial.get("description"):
                markdown += f" - {tutorial['description']}"
            
            markdown += "\n"
        
        markdown += "\n"
    
    # Add tags section
    markdown += "## Tags\n\n"
    
    for tag, tag_tutorials in sorted(categorized["by_tag"].items()):
        markdown += f"### #{tag}\n\n"
        
        for tutorial in sorted(tag_tutorials, key=lambda x: x.get("title", "")):
            relative_path = os.path.relpath(tutorial["path"], os.path.dirname(output_path))
            relative_path = relative_path.replace(".md", "/").replace("\\", "/")
            
            markdown += f"- [{tutorial['title']}]({relative_path})\n"
        
        markdown += "\n"
    
    # Add all tutorials section
    markdown += "## All Tutorials\n\n"
    
    for tutorial in sorted(tutorials, key=lambda x: x.get("title", "")):
        relative_path = os.path.relpath(tutorial["path"], os.path.dirname(output_path))
        relative_path = relative_path.replace(".md", "/").replace("\\", "/")
        
        markdown += f"- [{tutorial['title']}]({relative_path})"
        
        if tutorial.get("date"):
            markdown += f" ({tutorial['date']})"
        
        markdown += "\n"
    
    # Save the index page
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    logger.info(f"Generated index page at {output_path}")
    return output_path

def process_tutorials(tutorials_dir, output_dir):
    """
    Process all tutorials and generate index
    """
    # Ensure output directory exists
    ensure_directory(output_dir)
    
    # Scan for tutorials
    tutorial_files = scan_tutorials(tutorials_dir)
    
    # Process markdown files
    markdown_tutorials = []
    for md_file in tutorial_files["markdown"]:
        metadata = extract_metadata_from_markdown(md_file)
        markdown_tutorials.append(metadata)
        
        # Copy the file to output directory if needed
        if tutorials_dir != output_dir:
            rel_path = os.path.relpath(md_file, tutorials_dir)
            dest_path = os.path.join(output_dir, rel_path)
            ensure_directory(os.path.dirname(dest_path))
            shutil.copy2(md_file, dest_path)
            
            # Update the path in metadata
            metadata["path"] = dest_path
    
    # Process Jupyter notebooks
    jupyter_tutorials = []
    for ipynb_file in tutorial_files["jupyter"]:
        # Convert to markdown
        md_path = convert_jupyter_to_markdown(ipynb_file, output_dir)
        
        if md_path:
            metadata = extract_metadata_from_markdown(md_path)
            jupyter_tutorials.append(metadata)
    
    # Combine all tutorials
    all_tutorials = markdown_tutorials + jupyter_tutorials
    
    # Generate index page
    index_path = os.path.join(output_dir, "index.md")
    generate_index_page(all_tutorials, index_path)
    
    # Save metadata for all tutorials
    metadata_path = os.path.join(output_dir, "tutorials_metadata.json")
    save_json(all_tutorials, metadata_path)
    
    return {
        "total_tutorials": len(all_tutorials),
        "markdown_tutorials": len(markdown_tutorials),
        "jupyter_tutorials": len(jupyter_tutorials),
        "index_path": index_path,
        "metadata_path": metadata_path
    }

def main():
    """Main function to orchestrate tutorial indexing"""
    logger.info("Starting tutorial indexing process")
    
    try:
        # Configuration
        tutorials_dir = os.path.join(config.paths.content_dir, "tutorials")
        output_dir = os.path.join(config.paths.content_dir, "tutorials")
        
        # Process tutorials
        logger.info(f"Processing tutorials from {tutorials_dir}...")
        result = process_tutorials(tutorials_dir, output_dir)
        
        logger.info(f"Processed {result['total_tutorials']} tutorials:")
        logger.info(f"- {result['markdown_tutorials']} markdown tutorials")
        logger.info(f"- {result['jupyter_tutorials']} Jupyter notebooks converted to markdown")
        logger.info(f"Generated index page at {result['index_path']}")
        logger.info(f"Saved metadata to {result['metadata_path']}")
        
    except Exception as e:
        logger.error(f"Error in main tutorial indexing process: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()