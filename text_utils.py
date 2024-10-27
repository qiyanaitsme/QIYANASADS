import re


def normalize_text(text):
    return ' '.join(text.replace('\n', ' ').split())


def check_status(current_status, template_status, check_mode='exact'):
    if check_mode == 'url':
        template_url = template_status.split(' - ')[-1].strip()
        current_url = current_status.split(' - ')[-1].strip()
        return current_url == template_url
    return current_status == template_status


def check_pinned_post(current_post, template_post):
    return normalize_text(current_post) == normalize_text(template_post)


def extract_user_id(text):
    patterns = [
        r'(?:lolz\.live|zelenka\.guru|lolz\.guru|lzt\.market|lolz\.market|zelenka\.market)/members/(\d+)',
        r'(?:lolz\.live|zelenka\.guru|lolz\.guru|lzt\.market|lolz\.market|zelenka\.market)/(\d+)',
        r'^(\d+)$'
    ]

    for pattern in patterns:
        if match := re.search(pattern, text):
            return match.group(1)
    return None