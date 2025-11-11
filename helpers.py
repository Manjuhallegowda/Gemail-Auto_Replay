from config import KEYWORDS

def categorize_email(subject):
    """
    Categorizes an email based on the keywords in its subject.

    Args:
        subject (str): The subject of the email.

    Returns:
        str: The category of the email, or "Other" if no keyword is found.
    """
    if subject:
        for keyword in KEYWORDS:
            if keyword.lower() in subject.lower():
                return keyword.capitalize()
    return "Other"
