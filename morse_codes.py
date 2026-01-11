"""
Morse Code Dictionary Module
=============================
This module contains the universal Morse code patterns for A-Z and 0-9.
Each pattern is represented as a string where:
- '.' (dot) = short signal
- '-' (dash) = long signal (typically 3x the duration of a dot)

Usage:
    from morse_codes import MORSE_CODE, get_morse_pattern

    pattern = get_morse_pattern('S')  # Returns '...'
    pattern = get_morse_pattern('5')  # Returns '.....'
"""

# Universal International Morse Code Dictionary
MORSE_CODE = {
    # Letters A-Z
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',

    # Numbers 0-9
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.',

    # Special characters (optional, for future enhancement)
    '.': '.-.-.-', ',': '--..--', '?': '..--..',
    '/': '-..-.', '@': '.--.-.', ' ': '/'
}

# Reverse mapping: Morse pattern to character
REVERSE_MORSE_CODE = {v: k for k, v in MORSE_CODE.items()}


def get_morse_pattern(character):
    """
    Get the Morse code pattern for a given character.

    Args:
        character (str): A single character (A-Z, 0-9)

    Returns:
        str: Morse code pattern or None if character not found

    Example:
        >>> get_morse_pattern('S')
        '...'
        >>> get_morse_pattern('O')
        '---'
    """
    return MORSE_CODE.get(character.upper())


def get_character_from_morse(pattern):
    """
    Get the character corresponding to a Morse code pattern.

    Args:
        pattern (str): Morse code pattern (e.g., '...')

    Returns:
        str: Character or None if pattern not found

    Example:
        >>> get_character_from_morse('...')
        'S'
    """
    return REVERSE_MORSE_CODE.get(pattern)


def get_expected_timing(character, dot_duration=0.1):
    """
    Calculate expected timing for a character's Morse pattern.

    Standard Morse timing rules:
    - Dot duration: base unit
    - Dash duration: 3 × dot duration
    - Gap between dots/dashes within a character: 1 × dot duration
    - Gap between characters: 3 × dot duration
    - Gap between words: 7 × dot duration

    Args:
        character (str): Character to get timing for
        dot_duration (float): Base dot duration in seconds

    Returns:
        dict: Expected timing information

    Example:
        >>> get_expected_timing('S', 0.1)
        {'pattern': '...', 'total_duration': 0.5, 'num_elements': 3}
    """
    pattern = get_morse_pattern(character)
    if not pattern:
        return None

    total_duration = 0
    num_elements = len(pattern)

    for i, element in enumerate(pattern):
        if element == '.':
            total_duration += dot_duration
        elif element == '-':
            total_duration += 3 * dot_duration

        # Add inter-element gap (except after last element)
        if i < num_elements - 1:
            total_duration += dot_duration

    return {
        'pattern': pattern,
        'total_duration': total_duration,
        'num_elements': num_elements,
        'dots': pattern.count('.'),
        'dashes': pattern.count('-')
    }


def validate_morse_sequence(presses, expected_pattern, tolerance=0.3):
    """
    Validate if a sequence of press durations matches a Morse pattern.

    Args:
        presses (list): List of press durations in seconds
        expected_pattern (str): Expected Morse pattern (e.g., '...')
        tolerance (float): Tolerance factor (0.3 = 30% variation allowed)

    Returns:
        bool: True if sequence matches pattern within tolerance

    Example:
        >>> validate_morse_sequence([0.1, 0.1, 0.1], '...', 0.3)
        True
    """
    if len(presses) != len(expected_pattern):
        return False

    # Estimate dot duration from the presses
    dot_duration = min(presses)

    for i, (press, element) in enumerate(zip(presses, expected_pattern)):
        if element == '.':
            expected = dot_duration
        else:  # dash
            expected = 3 * dot_duration

        # Check if press is within tolerance
        lower_bound = expected * (1 - tolerance)
        upper_bound = expected * (1 + tolerance)

        if not (lower_bound <= press <= upper_bound):
            return False

    return True


def display_morse_chart():
    """Display a formatted Morse code chart for reference."""
    print("\n" + "=" * 50)
    print("UNIVERSAL MORSE CODE CHART")
    print("=" * 50)

    print("\nLETTERS:")
    for i in range(0, 26, 3):
        row = []
        for j in range(3):
            if i + j < 26:
                char = chr(65 + i + j)
                morse = MORSE_CODE[char]
                row.append(f"{char}: {morse:6s}")
        print("  ".join(row))

    print("\nNUMBERS:")
    for i in range(0, 10, 5):
        row = []
        for j in range(5):
            if i + j < 10:
                char = str(i + j)
                morse = MORSE_CODE[char]
                row.append(f"{char}: {morse:6s}")
        print("  ".join(row))

    print("\n" + "=" * 50)
    print("Legend: . = dot (short)  - = dash (long, 3x dot)")
    print("=" * 50 + "\n")


# For testing the module
if __name__ == "__main__":
    display_morse_chart()

    # Test examples
    print("\nTest Examples:")
    print(f"Pattern for 'SOS': {get_morse_pattern('S')}-{get_morse_pattern('O')}-{get_morse_pattern('S')}")
    print(f"Timing for 'A': {get_expected_timing('A', 0.1)}")