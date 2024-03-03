import gradio as gr
import os
import re

def file_extension_check(filename, extension):
    return os.path.splitext(filename)[1].lower() == extension

def save_results_to_file(results, filename="output.txt"):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(results)
    return filename  # Gradio will handle this path and allow the user to download the file

def find_txt_files_with_tag(directory, tags, search_mode='exact'):
    matching_files = []
    matching_details = []
    tag_counts = {}

    # Splitting input_tag into a list of tags
    tags = [tag.strip() for tag in tags.split(',')]

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if file_extension_check(filename, '.txt'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().lower()
                    # Normalize content tags for comparison
                    content_tags = [t.strip().lower() for t in content.split(',')]
                    found_tags = []
                    if search_mode == 'regex':
                        for tag_pattern in tags:
                            pattern = re.compile(tag_pattern)
                            for tag in content_tags:
                                if pattern.search(tag):
                                    found_tags.append(tag)
                    else:
                        for tag in tags:  # Check each input tag
                            if search_mode == 'exact' and tag in content_tags:
                                found_tags.append(tag)
                            elif search_mode == 'partial':
                                # Add all content tags that include the input tag as a substring
                                found_tags.extend([t for t in content_tags if tag in t])

                    if found_tags:
                        # Remove duplicates and sort for consistent ordering
                        found_tags_unique_sorted = sorted(set(found_tags))
                        matching_details.append(f"{filename}: {', '.join(found_tags_unique_sorted)}")
                        for ft in found_tags_unique_sorted:
                            # Count the number of occurrences of each matching tag
                            tag_counts[ft] = tag_counts.get(ft, 0) + 1

    if search_mode != 'exact':
        tag_summary = ", ".join([f"{key}:{value}" for key, value in tag_counts.items()])
        result_summary = f"{tag_summary}\nResults:\n" + "\n".join(matching_details)
        return result_summary

    # Return joined list if exact match is selected, as there's no need for a summary count in this case
    return "\n".join(matching_details)

def replace_tag_in_files(directory, input_tags, new_tag, replace_mode):
    modified_files = []
    changes_made = []  # Collects changes made per file
    warning_message = None

    # Process tags based on the mode
    if replace_mode in ['partial', 'regex']:
        input_tags = [tag for tag in input_tags.split(',')]
    else:
        input_tags = [tag.strip() for tag in input_tags.split(',')]  # For 'full', strip spaces

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if file_extension_check(filename, '.txt'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().lower()  # Convert to lower case to do a case-insensitive search
                    updated_content = content
                    file_changes = []  # Collects changes for this specific file

                    if replace_mode == 'full':
                        for tag in input_tags:
                            pattern = fr'\b{re.escape(tag)}\b'
                            matches = re.findall(pattern, content, flags=re.IGNORECASE)
                            if matches:
                                updated_content = re.sub(pattern, new_tag, updated_content, flags=re.IGNORECASE)
                                for match in matches:
                                    file_changes.append(f"{match} -> {new_tag}")
                    
                    elif replace_mode == 'partial':
                        warning_message = "Warning: Partial replace mode can result in unexpected changes."
                        content_tags = set(content.split(','))
                        for tag in input_tags:
                            pattern = tag
                            matches = [ct for ct in content_tags if tag in ct]
                            if matches:
                                updated_content = updated_content.replace(tag, new_tag)
                                for match in matches:
                                    file_changes.append(f"{match} -> {match.replace(tag, new_tag)}")

                    elif replace_mode == 'regex':
                        content_tags = set(content.split(','))
                        for tag in input_tags:
                            pattern = tag
                            matches = [ct for ct in content_tags if re.findall(pattern, ct)] # re.findall(pattern, content)
                            if matches:
                                updated_content = re.sub(pattern, new_tag, updated_content)
                                for match in matches:
                                    file_changes.append(f"{match} -> {re.sub(pattern, new_tag, match)}")
                    
                    # If there were any changes, record them
                    if content != updated_content:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(updated_content)
                        modified_files.append(filename)
                        file_change_description = ', '.join(file_changes)
                        changes_made.append(f"{filename}: {file_change_description}")

    if warning_message:
        changes_made.insert(0, warning_message)
    return changes_made or ["No files modified."]

def search_for_tag(directory, input_tag, search_mode):
    result = find_txt_files_with_tag(directory, input_tag, search_mode)
    return "Results:\n" + (result if result else "No matches found.")

def replace_tag(directory, input_tag, new_tag, replace_mode):
    results = replace_tag_in_files(directory, input_tag, new_tag, replace_mode)
    return "Tags replaced in files:\n" + ("\n".join(results))

with gr.Blocks() as demo:
    with gr.Row():
        input_tag = gr.Textbox(label="Input Tag", placeholder="Enter the tag to search for")
        directory = gr.Textbox(label="Directory", placeholder="Enter the directory path")
        search_mode = gr.Radio(choices=['exact', 'partial', 'regex'], value='exact', label="Search Mode")
        search_button = gr.Button("Search")
    
    with gr.Row():
        new_tag = gr.Textbox(label="New Tag", placeholder="Enter the new tag")
        replace_mode = gr.Radio(choices=['full', 'partial', 'regex'], value='full', label="Replace Mode")
        replace_button = gr.Button("Replace Tag")
    
    output_search = gr.Textbox(label="Search Result", lines=10)
    output_replace = gr.Textbox(label="Replace Result", lines=10)
    download_button = gr.Button("Download Output")
    download_result = gr.File(label="Download Output")
    download_button.click(fn=save_results_to_file, inputs=output_search, outputs=download_result)
    search_button.click(fn=search_for_tag, inputs=[directory, input_tag, search_mode], outputs=output_search)
    replace_button.click(fn=replace_tag, inputs=[directory, input_tag, new_tag, replace_mode], outputs=output_replace)

demo.launch()