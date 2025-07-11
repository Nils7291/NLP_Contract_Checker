from functions.functions_preprocessing import (
    extract_paragraphs_and_sections,
    clean_sections_and_paragraphs)

import pandas as pd

class SectionTopicPredictor:
    def __init__(self, cosinemapper, topics):
        """
        Parameters:
        - model: dein CosineMapper mit predict()-Methode
        - catalogue_clean: DataFrame mit Spalte 'section_topic'
        """
        self.model = cosinemapper
        self.topics= topics

    def _preprocess_contract(self, text):
        """
        Führt Paragraph- und Abschnittsextraktion + Cleaning durch.
        """
        fake_row = {"content": text, "contract": 1}
        sections = extract_paragraphs_and_sections(fake_row)  # -> List[Dict]
        for section in sections:
            section["clean_section_content"] = clean_sections_and_paragraphs(section["section_content"])
        return sections

    def predict_contract(self, contract_text, return_topic_score=False):
        """
        contract_text: Volltext eines Vertrags (String)

        Rückgabe: DataFrame mit Feldern aus den extrahierten Sections + 'predicted_topic'
        """
        cont_exp = self._preprocess_contract(contract_text)
        return self.predict_sections(cont_exp, return_topic_score=return_topic_score)

    def predict_sections(self, cont_exp, return_topic_score=False):
        """
        cont_exp: Liste von Dicts mit mindestens 'section', 'section_content', 'clean_section_content'

        Rückgabe: DataFrame mit allen ursprünglichen Feldern + 'predicted_topic'
        """
        records = []

        for section in cont_exp:
            cleaned = section['clean_section_content']

            if return_topic_score:
                model_output = self.model.predict(cleaned, return_scores=True)

                top = max(model_output, key=lambda x: x[1])
                label = top[0]
                score = top[1]
                index = int(label) - 1 
            else:
                label = self.model.predict(cleaned, return_scores=False)
                index = int(label) - 1
                score = None

            topic = self.topics.iloc[index]

            record = {**section, "predicted_topic": topic}
            if return_topic_score:
                record["score"] = score

            records.append(record)

        return pd.DataFrame(records)
    
