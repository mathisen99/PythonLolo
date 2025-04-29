import re
import unicodedata

def sanitize_for_irc(text: str) -> str:
    """
    Sanitize text for IRC:
    - Remove carriage returns
    - Remove/replace markdown (bold, italics, code, blockquotes, lists)
    - Remove links, images
    - Replace bullets and excessive symbols
    - Remove control characters (keep emojis, unicode)
    - Collapse whitespace (except newlines)
    """
    clean = text.replace('\r', '')
    clean = re.sub(r'```(.*?)```', r'\1', clean, flags=re.DOTALL)
    clean = re.sub(r'`([^`]+)`', r'\1', clean)
    clean = re.sub(r'([*_]{1,2})(\S.*?\S)\1', r'\2', clean)
    clean = re.sub(r'^>\s?', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'!?\[[^\]]*\]\([^)]*\)', '', clean)
    clean = re.sub(r'^\s*[-*+]\s+', '- ', clean, flags=re.MULTILINE)
    clean = re.sub(r'[\u2022\u25CF\u25A0]+', '-', clean)  # bullets
    clean = re.sub(r'[\u200B-\u200D\uFEFF]', '', clean)   # zero-width chars
    clean = ''.join(c for c in clean if unicodedata.category(c)[0] != 'C')
    clean = re.sub(r'[ \t]+', ' ', clean)
    clean = re.sub(r' *\n *', '\n', clean)
    return clean.strip()


def split_irc_messages(text: str, maxlen: int = 400) -> list[str]:
    """
    Split a possibly multi-line message into IRC-safe lines, preserving line breaks as message boundaries.
    Each line is split further if it exceeds maxlen, never splitting in the middle of words.
    """
    sanitized = sanitize_for_irc(text)
    lines = sanitized.split('\n')
    messages = []
    for line in lines:
        words = line.split(' ')
        current = ''
        for word in words:
            if len(current) + len(word) + 1 > maxlen:
                if current:
                    messages.append(current.strip())
                current = word
            else:
                if current:
                    current += ' '
                current += word
        if current:
            messages.append(current.strip())
    return [m for m in messages if m]
