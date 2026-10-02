import pronouncing
import unicodedata
import re
import logging

# Setup logging
logging.basicConfig(filename='transliteration.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

# Common usage exceptions (fixed transliterations)
COMMON_WORDS = {
    'the': 'ذَا',
    'this': 'ذِسْ',
    'that': 'ذَتْ',
    'of': 'أُفْ',
    'and': 'أَنْدْ',
    'in': 'إِنْ',
    'to': 'تُو',
    'a': 'أَ',
    'is': 'إِزْ'
}

# Consonant mappings (Farsi letters removed)
CONSONANTS = {
    'b': 'ب', 'd': 'د', 'f': 'ف', 'g': 'ج', 'h': 'ه', 'j': 'ج', 'k': 'ك',
    'l': 'ل', 'm': 'م', 'n': 'ن', 'r': 'ر', 's': 'س', 't': 'ت', 'w': 'و',
    'y': 'ي', 'z': 'ز', 'sh': 'ش'
}

# Special cases (adjusted for Arabic-only)
SPECIAL_CONSONANTS = {
    'th_voiced': 'ذ',            # e.g., 'the'
    'th_voiceless': 'ث',         # e.g., 'think'
    'p': 'ب',                    # Default 'p' to 'ب'
    'p_breathy': 'ف',            # Approx. for 'psycho'
    'v_unvoiced': 'ف',           # e.g., 'versus'
    'v_voiced': 'ب'              # e.g., 'delves'
}

# Vowel mappings
VOWELS = {
    'AE': 'َ', 'AA': 'ا', 'IY': 'ي', 'IH': 'ِ',
    'EH': 'ِ', 'EY': 'ي', 'AO': 'و', 'OW': 'و',
    'UH': 'ُ', 'UW': 'و', 'ER': 'ر', 'AY': 'ي', 'AW': 'و'
}

# Minimal contextual forms for now
LETTER_FORMS = {
    'ب': {'isolated': 'ب'}, 'د': {'isolated': 'د'},
    'ذ': {'isolated': 'ذ'}, 'ث': {'isolated': 'ث'},
    'ف': {'isolated': 'ف'}, 'ج': {'isolated': 'ج'},
    'ك': {'isolated': 'ك'}, 'ل': {'isolated': 'ل'},
    'م': {'isolated': 'م'}, 'ن': {'isolated': 'ن'},
    'ر': {'isolated': 'ر'}, 'س': {'isolated': 'س'},
    'ت': {'isolated': 'ت'}, 'و': {'isolated': 'و'},
    'ي': {'isolated': 'ي'}, 'ز': {'isolated': 'ز'},
    'ه': {'isolated': 'ه'}, 'ش': {'isolated': 'ش'}
}

def get_phonemes(word):
    phonemes = pronouncing.phones_for_word(word.lower())
    if phonemes:
        return phonemes[0].split()
    logging.warning(f"No phonemes for '{word}', using spelling fallback")
    return [char for char in word.lower()]

def is_voiced_v(word, index):
    if index > 0 and index < len(word) - 1:
        prev_char = word[index - 1].lower()
        next_char = word[index + 1].lower()
        voiced = {'a', 'e', 'i', 'o', 'u', 'b', 'd', 'g', 'j', 'l', 'm', 'n', 'r', 'w', 'y', 'z'}
        return prev_char in voiced or next_char in voiced
    return False

def transliterate_word(word):
    if word.lower() in COMMON_WORDS:
        return COMMON_WORDS[word.lower()]
    
    phonemes = get_phonemes(word)
    result = []
    i = 0
    while i < len(phonemes):
        phoneme = phonemes[i]
        if phoneme.startswith('DH'):
            result.append(SPECIAL_CONSONANTS['th_voiced'])
        elif phoneme.startswith('TH'):
            result.append(SPECIAL_CONSONANTS['th_voiceless'])
        elif phoneme in ['B', 'D', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'R', 'S', 'T', 'W', 'Y', 'Z']:
            char = phoneme.lower()[0]
            result.append(CONSONANTS.get(char, char))
        elif phoneme == 'P':
            result.append(SPECIAL_CONSONANTS['p_breathy'] if word.lower().startswith('psych') else SPECIAL_CONSONANTS['p'])
        elif phoneme == 'V':
            result.append(SPECIAL_CONSONANTS['v_voiced'] if is_voiced_v(word, i) else SPECIAL_CONSONANTS['v_unvoiced'])
        elif phoneme in VOWELS:
            result.append(VOWELS[phoneme])
        else:
            result.append(phoneme.lower())
        i += 1
    
    output = ''.join(LETTER_FORMS.get(c, {}).get('isolated', c) for c in result)
    logging.info(f"Transliterated '{word}' to '{output}'")
    return output

def transliterate_text(text):
    words = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    return ''.join(transliterate_word(word) if word.isalpha() else word for word in words)

def main():
    test_text = "In this part of Helen Rollins Psychocinema, she delves into capitalist ideology."
    print("Original:", test_text)
    transliterated = transliterate_text(test_text)
    print("Transliterated:", transliterated)

    with open('transliteration_output.txt', 'w', encoding='utf-8') as f:
        f.write(transliterated)

if __name__ == "__main__":
    main()
