import re
from emojis import emojis


def sanitize_input(msg: str):
    new_msg = re.sub(r'[’`‵ʼ‘]', '\'', msg)  # fix singlequote characters
    new_msg = re.sub(r'[“”＂❝❞]', '"', new_msg)  # fix double quote characters
    new_msg = re.sub(r'[   ]', ' ', new_msg)  # replace ENSP, EMSP, and non-breaking space
    new_msg = re.sub(r'…', '...', new_msg)  # fix ellipses
    return new_msg


def extract_emoji(content: str):
    # get using library
    emoji = emojis.get(content)

    # get using regex
    if (emoji is None):
        emoji = re.match(r'<.*:\w*:\d*>', content)
    if (emoji is None):
        return ''
    return emoji


def clean_case(text: str):
    return re.compile("^"+re.escape(text)+"$", re.IGNORECASE)


def clean_search(text: str):
    return re.compile(".*" + re.escape(text) + ".*", re.IGNORECASE)