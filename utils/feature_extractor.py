import re


def extract_features(url):

    features = []

    # URL Length
    features.append(len(url))

    # HTTPS Check
    features.append(
        1 if url.startswith("https")
        else 0
    )

    # Dot Count
    features.append(url.count("."))

    # Hyphen Count
    features.append(url.count("-"))

    # Slash Count
    features.append(url.count("/"))

    # Contains @
    features.append(
        1 if "@" in url
        else 0
    )

    # Contains IP
    ip_pattern = r'(\d{1,3}\.){3}\d{1,3}'

    features.append(
        1 if re.search(ip_pattern, url)
        else 0
    )

    return features