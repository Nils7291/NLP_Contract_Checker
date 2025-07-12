from torch.utils.data import Dataset

class TextLabelDataset(Dataset):
    def __init__(self, texts, labels):
        """
        Initializes the dataset with texts and labels.

        Parameters:
        - texts: List of input text strings
        - labels: Corresponding list of labels
        """
        self.texts = texts
        self.labels = labels

    def __len__(self):
        """
        Returns the number of samples in the dataset.
        """
        return len(self.texts)

    def __getitem__(self, idx):
        """
        Retrieves the text and label at the specified index.

        Parameters:
        - idx: Index of the sample to retrieve

        Returns:
        - A dictionary with 'text' and 'label' keys
        """
        return {
            "text": self.texts[idx],
            "label": self.labels[idx]
        }
