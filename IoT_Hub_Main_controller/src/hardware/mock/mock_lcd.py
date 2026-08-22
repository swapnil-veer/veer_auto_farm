class MockLCD:

    def __init__(self):
        self.lines = {
            1: "",
            2: "",
            3: "",
            4: ""
        }
        self.custom_chars = {}

    def write_line(self, line_no, text):
        self.lines[line_no] = text[:20]

    def clear(self):
        for line in self.lines:
            self.lines[line] = ""

    def get_lines(self):
        return self.lines

    def create_char(self, location, charmap):
        """
        location: int (0–7) slot for custom char
        charmap: list of 8 integers (each 5 bits wide) representing rows
        """
        if not (0 <= location <= 7):
            raise ValueError("Location must be between 0 and 7")
        if len(charmap) != 8:
            raise ValueError("Charmap must have 8 rows")
        self.custom_chars[location] = charmap
        return charmap  # <-- return the stored bitmap