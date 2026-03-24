def preprocess_text(raw_text):
    """
    Cleans and normalizes extracted contract text.
    """

    cleaned_text = raw_text.replace("\n", " ")
    cleaned_text = " ".join(cleaned_text.split())

    return cleaned_text
