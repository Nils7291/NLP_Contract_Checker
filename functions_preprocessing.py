def extract_paragraphs_and_sections(row, col='content', contract_col='contract', print_steps = False):
    import re

    text = row[col]
    if contract_col ==None:
        contract_id= 1
    else:
        contract_id = row['contract']
    lines = text.splitlines()
    paragraphs = []
    current_para_lines = []
    current_para_number = 0
    current_para_match = None
    match_pat_type_1 = True
    match_pat_type_2 = True
    match_pat_type_3 = True
    para_mode = None

    # 1. extract paragraphs

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
            # Noch kein Modus festgelegt: beides probieren
            match_main = re.match(rf'(§\s*(\d+))(?!\d)|\b(\d+)\.(?!\d)', line)
            if match_main:
                if match_main.group(1):  # § X
                    para_mode = "symbol"
                elif match_main.group(3):  # X.
                    para_mode = "number"
       

        if match_main:
            if current_para_lines:
                paragraphs.append((current_para_number, ' '.join(current_para_lines), current_para_match))
            current_para_number = match_main.group(0).strip().lstrip('§').rstrip('.').strip()  # e.g § 2 lorem ipsum --> 2
            current_para_lines = [line]                                                        # e.g § 2 lorem ipsum --> § 2 lorem impsum
            current_para_match = match_main.group(0).strip()                                   # e.g § 2 lorem ipsum --> § 2
        elif current_para_lines:
            current_para_lines.append(line)

    if current_para_lines:
        paragraphs.append((current_para_number, ' '.join(current_para_lines), current_para_match))

    rows = []
    seen_sections = set()  # (contract_id, para_num, section_id)

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
        

        for match in matches:
            # hole entweder dezimale section (z. B. 1.1) oder Klammer-section (z. B. (1))
            section_id = match.group(1) or match.group(2) or match.group(3)
            start = match.start()

            # Unterscheide die Formate
            if match.group(1) and match_pat_type_1:  # Dezimal: z. B. "1.5"
                try:
                    section_suffix = int(section_id.split(".")[1])
                except (IndexError, ValueError):
                    continue  # überspringen bei Fehler
                match_pat_type_2 = False # If first pattern type detected only look for this one
                match_pat_type_3 = False

                # verbiete z. B. "1.50"
               # if re.match(rf'{para_num}\.\d{{2,}}$', section_id):
                #    continue

            elif match.group(2) and match_pat_type_2:  # Klammer: z. B. "(2)"
                try:
                    section_suffix = int(section_id.strip("()")) 
                    section_id = f'({section_suffix})'  # Einheitliches Format für Ausgabe
                except ValueError:
                    continue
                match_pat_type_1 = False # If second pattern type detected only look for this one
                match_pat_type_3 = False
            elif para_mode == "symbol" and match.group(3) and match_pat_type_3:  # 1. (nur bei mode=symbol)
                if print_steps:
                    print(section_id)
                try:
                    section_suffix = int(section_id.split(".")[0])
                    section_id = f'{section_suffix}.'  # für Klarheit
                except ValueError:
                    continue
                match_pat_type_1 = False # If third pattern type detected only look for this one
                match_pat_type_2 = False

            else:
                continue  # kein gültiges Format

            # Nur nächste Zahl zulassen
            if last_section_number != 0 and section_suffix != last_section_number + 1:
                continue

            section_key = (contract_id, para_num, section_id)
            if section_key in seen_sections:
                continue

            seen_sections.add(section_key)
            positions.append((start, section_id))
            last_section_number = section_suffix


        # Add end position
        positions.append((len(para_text), None))
        positions = sorted(positions)
        if print_steps:
            print(f'positions = {positions}')
            print('###########')

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
    import re
    paragraph_text = group['paragraph_content'].iloc[0]
    section_texts = group['section_content'].tolist()

    # No Sections (single paragraph)
    if len(section_texts) == 1 and group['section'].iloc[0] == "no sections use paragraph":
        # find sentence end
        match = re.search(r'\b(Der|Die|Das|Es|Ein|Eine)\s+[A-ZÄÖÜ][a-zäöü]+\b', paragraph_text)
        if match:
            title = paragraph_text[:match.start()].strip()
        else:
            # Fallback: to first verb or 8 words
            title = ' '.join(paragraph_text.split()[:8])
        return pd.Series([title] * len(group), index=group.index)

    # secction split
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
    remove_stopwords =False,
    apply_stemming=False
):
    if not isinstance(text, str):
        return ""

    if to_lower:
        text = text.lower()

    if remove_paragraph_markers:
        # Remove paragraph indicators like "§ 1", "1.", "1.1" etc.
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
        text = remove_stopwords(text, stopwords=STOPWORDS) # !!!!!! Englische Stopwörter  !!!!!!!

    if apply_stemming:
        text = stem_text(text)

    return text.strip()
