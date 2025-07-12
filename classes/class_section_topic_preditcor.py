from functions.functions_preprocessing import (
    extract_paragraphs_and_sections,
    clean_sections_and_paragraphs)

import pandas as pd

class SectionTopicPredictor:
    def __init__(self, cosinemapper, topics):
        """
        Parameters:
        - model: your CosineMapper with a predict() method
        - catalogue_clean: DataFrame with a 'section_topic' column
        """
        self.model = cosinemapper
        self.topics= topics

    def _preprocess_contract(self, text):
        """
        Performs paragraph and section extraction and cleaning.
        """
        fake_row = {"content": text, "contract": 1}
        sections = extract_paragraphs_and_sections(fake_row)  # -> List[Dict]
        for section in sections:
            section["clean_section_content"] = clean_sections_and_paragraphs(section["section_content"])
        return sections

    def predict_contract(self, contract_text, return_topic_score=False):
        """
        contract_text: Full text of a contract (string)

        Returns: DataFrame with fields from the extracted sections + 'predicted_topic'
        """
        cont_exp = self._preprocess_contract(contract_text)
        return self.predict_sections(cont_exp, return_topic_score=return_topic_score)

    def predict_sections(self, cont_exp, return_topic_score=False):
        """
        cont_exp: List of dicts with at least 'section', 'section_content', 'clean_section_content'

        Returns: DataFrame with all original fields + 'predicted_topic'
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
