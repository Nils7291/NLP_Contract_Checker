import re
import pandas as pd
from gensim.parsing.preprocessing import (
    STOPWORDS,
    strip_tags, strip_numeric, strip_punctuation,
    strip_multiple_whitespaces, remove_stopwords,
    strip_short, stem_text
)


def extract_paragraphs_and_sections(row, col='content', contract_col='contract', print_steps=False):
    """
    Splits the input text into paragraphs and sub-sections based on paragraph markers.

    Parameters:
    - row: A DataFrame row containing the contract text
    - col: Column name for the raw text content (default: 'content')
    - contract_col: Column name for contract ID (default: 'contract')
    - print_steps: If True, prints debug info

    Returns:
    - A list of dictionaries with keys:
      ['contract', 'paragraph', 'paragraph_content', 'section', 'section_content']
    """
    import re

    # ------------------------------------------------------
    # 1. Initialize variables and prepare input text
    # ------------------------------------------------------
    text = row[col]
    contract_id = row['contract'] if contract_col else 1
    lines = text.splitlines()
    paragraphs = []
    current_para_lines = []
    current_para_number = 0
    current_para_match = None
    match_pat_type_1 = True
    match_pat_type_2 = True
    match_pat_type_3 = True
    para_mode = None

    # ------------------------------------------------------
    # 2. Detect and group text lines into paragraphs
    #    based on numeric or symbol-based paragraph markers
    # ------------------------------------------------------
    for line in lines:
        line = line.strip()
        if not line:
            continue

        search_for = str(int(current_para_number) + 1)

        if para_mode == "symbol":
            if search_for:
                match_main = re.match(rf'§\s*{search_for}(?!\d)', line)
        elif para_mode == "number":
            if search_for:
                match_main = re.match(rf'\b{search_for}\.(?!\d)', line)
        else:
            match_main = re.match(rf'(§\s*(\d+))(?!\d)|\b(\d+)\.(?!\d)', line)
            if match_main:
                if match_main.group(1):
                    para_mode = "symbol"
                elif match_main.group(3):
                    para_mode = "number"

        if match_main:
            if current_para_lines:
                paragraphs.append((current_para_number, ' '.join(current_para_lines), current_para_match))
            current_para_number = match_main.group(0).strip().lstrip('§').rstrip('.').strip()
            current_para_lines = [line]
            current_para_match = match_main.group(0).strip()
        elif current_para_lines:
            current_para_lines.append(line)

    if current_para_lines:
        paragraphs.append((current_para_number, ' '.join(current_para_lines), current_para_match))

    # ------------------------------------------------------
    # 3. Extract sub-sections within each paragraph
    #   based on the detected paragraph mode:
    #    - "number": numbered paragraphs like 1., 2., ...
    #    - "symbol": paragraphs marked with § and sub-numbers
    # ------------------------------------------------------
    rows = []
    seen_sections = set()

    for para_num, para_text, para_match in paragraphs:

        if para_mode == "number":
            matches = list(re.finditer(rf'(?:(?<=\s)|(?<=^))({para_num}\.\d{{1}})(?![\dA-Za-z])|\((\d+)\)', para_text))
        if para_mode == "symbol":
            matches = list(re.finditer(rf'(?:(?<=\s)|(?<=^))({para_num}\.\d{{1}})(?![\dA-Za-z])|\((\d+)\)|\b(\d+)\.(?!\d)', para_text))

        if print_steps:
            print(para_num)
            print(seen_sections)
            print(para_text)
            print(matches)

        # Fallback if no sub-sections are found
        if not matches:
            rows.append({
                'contract': contract_id,
                'paragraph': para_match,
                'paragraph_content': para_text.strip(),
                'section': "no sections use paragraph",
                'section_content': para_text.strip()
            })
            continue

        positions = []
        last_section_number = 0

        # ------------------------------------------------------
        # 4. Identify valid sub-section markers and their positions
        # ------------------------------------------------------
        for match in matches:
            section_id = match.group(1) or match.group(2) or match.group(3)
            start = match.start()

            if match.group(1) and match_pat_type_1:
                try:
                    section_suffix = int(section_id.split(".")[1])
                except (IndexError, ValueError):
                    continue
                match_pat_type_2 = False
                match_pat_type_3 = False

            elif match.group(2) and match_pat_type_2:
                try:
                    section_suffix = int(section_id.strip("()"))
                    section_id = f'({section_suffix})'
                except ValueError:
                    continue
                match_pat_type_1 = False
                match_pat_type_3 = False

            elif para_mode == "symbol" and match.group(3) and match_pat_type_3:
                if print_steps:
                    print(section_id)
                try:
                    section_suffix = int(section_id.split(".")[0])
                    section_id = f'{section_suffix}.'
                except ValueError:
                    continue
                match_pat_type_1 = False
                match_pat_type_2 = False
            else:
                continue

            # Skip if section sequence is broken or already seen
            if last_section_number != 0 and section_suffix != last_section_number + 1:
                continue

            section_key = (contract_id, para_num, section_id)
            if section_key in seen_sections:
                continue

            seen_sections.add(section_key)
            positions.append((start, section_id))
            last_section_number = section_suffix

        positions.append((len(para_text), None))
        positions = sorted(positions)

        if print_steps:
            print(f'positions = {positions}')
            print('###########')

        # ------------------------------------------------------
        # 5. Slice paragraph into sub-sections based on positions
        # ------------------------------------------------------
        for i in range(len(positions) - 1):
            start_pos = positions[i][0]
            end_pos = positions[i + 1][0]
            section_id = positions[i][1]
            section_text = para_text[start_pos:end_pos].strip()

            rows.append({
                'contract': contract_id,
                'paragraph': para_match,
                'paragraph_content': para_text.strip(),
                'section': section_id,
                'section_content': section_text
            })

    return rows


def extract_title_fixed(group):
    """
    Extracts the title from the paragraph by subtracting section content.

    Parameters:
    - group: Grouped DataFrame row with 'paragraph_content' and 'section_content'

    Returns:
    - A pandas Series containing the extracted title repeated for each section
    """
    import re
    paragraph_text = group['paragraph_content'].iloc[0]
    section_texts = group['section_content'].tolist()

    if len(section_texts) == 1 and group['section'].iloc[0] == "no sections use paragraph":
        match = re.search(r'\b(Der|Die|Das|Es|Ein|Eine)\s+[A-ZÄÖÜ][a-zäöü]+\b', paragraph_text)
        if match:
            title = paragraph_text[:match.start()].strip()
        else:
            title = ' '.join(paragraph_text.split()[:8])
        return pd.Series([title] * len(group), index=group.index)

    for section in section_texts:
        paragraph_text = paragraph_text.replace(section, '')
    title = paragraph_text.strip()
    return pd.Series([title] * len(group), index=group.index)


def clean_sections_and_paragraphs(
    text,
    remove_paragraph_markers=True,
    to_lower=True,
    remove_tags=True,
    remove_numbers=True,
    remove_punctuation=True,
    remove_extra_whitespace=True,
    strip_short_words=False,
    remove_stopwords=False,
    apply_stemming=False
):
    """
    Cleans legal text for downstream NLP processing.

    Parameters:
    - text: The raw string to clean
    - remove_paragraph_markers: If True, removes legal markers like '§ 1' or '1.1'
    - to_lower: If True, converts text to lowercase
    - remove_tags: If True, removes HTML/XML tags
    - remove_numbers: If True, removes all digits
    - remove_punctuation: If True, removes punctuation characters
    - remove_extra_whitespace: If True, normalizes multiple whitespaces
    - strip_short_words: If True, removes words shorter than 3 characters
    - remove_stopwords: If True, removes stopwords (⚠ uses English stopwords)
    - apply_stemming: If True, applies stemming using gensim

    Returns:
    - A cleaned string
    """
    if not isinstance(text, str):
        return ""

    if to_lower:
        text = text.lower()

    if remove_paragraph_markers:
        text = re.sub(r'^(§?\s*\d+[a-zA-Z]*[.)]?(\s*\(?\d+[.)]?)?)', '', text)
        text = re.sub(r'\(?\b\d{1,2}(\.\d{1,2})?\)?', '', text)

    if remove_tags:
        text = strip_tags(text)

    if remove_numbers:
        text = strip_numeric(text)

    if remove_punctuation:
        text = strip_punctuation(text)

    if remove_extra_whitespace:
        text = strip_multiple_whitespaces(text)

    if strip_short_words:
        text = strip_short(text, minsize=3)

    if remove_stopwords:
        text = remove_stopwords(text, stopwords=STOPWORDS)  # ⚠ English stopwords only

    if apply_stemming:
        text = stem_text(text)

    return text.strip()
