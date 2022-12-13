import collections
from dataclasses import dataclass
import os
import re
import sys

import prompt_toolkit as pt


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class Abbreviation:
    abbr: str
    defn: str
    expl: str

    def _show(self, text):
        """Show with explanation if present."""
        return f'{text} {self.expl}' if self.expl else text

    def show_defn(self):
        return self._show(self.defn)

    def show_abbr(self):
        return self._show(f'{self.abbr}: {self.defn}')


def split_expl(entry: str):
    """Split up an abbreviation or definition with an explanation."""
    # e.g. MO (medical officer): Doctor
    if "(" in entry:  # )
         l, r = entry.split(" (", 1)  # )
         return l.strip(), "(" + r.strip()  # )
    else:
         return entry, ""


class LineParser:
    def __init__(self):
        self.bc = 0
        self.lhs = []
        self.rhs = []
        self.section = self.lhs
        self.current = ''
        self.lhs_abbrs = None

    def finish_word(self):
        self.section.append(self.current.strip())
        self.current = ''

    def parse(self, line):
        """Parse a line into abbreviations and definitions."""
        toks = re.split(r'([(),:]|->)', line)
        toks = list(filter(None, toks))
        for tok in toks:
            if tok == '(':  # )
                self.current += tok
                self.bc += 1
            elif tok == ')':
                self.current += tok
                if self.bc:
                    self.bc -= 1
                else:
                    raise ParseError("Mismatched parentheses:", line)
            elif self.bc:
                self.current += tok
            elif tok == ':':
                self.lhs_abbrs = True
                self.finish_word()
                self.section = self.rhs
            elif tok == '->':
                self.lhs_abbrs = False
                self.finish_word()
                self.section = self.rhs
            elif tok == ",":
                self.finish_word()
            else:
                self.current += tok
        self.finish_word()
        if self.lhs_abbrs is None:
            raise ParseError("Missing abbreviation/definition separator:", line)
        return (self.lhs, self.rhs) if self.lhs_abbrs else (self.rhs, self.lhs)


class Abbreviations:
    def __init__(self):
        self.abbrevs = collections.defaultdict(set)
        self.reverse = collections.defaultdict(set)

    def add(self, abbr, defn):
        """Add an abbreviation and definition pair."""
        abbr, expl1 = split_expl(abbr)
        defn, expl2 = split_expl(defn)
        expl = " ".join((expl1, expl2)).strip()
        out = Abbreviation(abbr, defn, expl)
        self.abbrevs[abbr.upper()].add(out)

        for d in defn.split(" "):
            self.reverse[d.upper()].add(out)

    def add_line(self, line):
        """Add a line read from a data file."""
        line = line.strip()
        if line.startswith("#") or line == "":
            return
        abbrs, defs = LineParser().parse(line)
        for a in abbrs:
            for d in defs:
                self.add(a, d)

    def lookup_abbr(self, abbr):
        abbr = abbr.strip().upper()
        return self.abbrevs[abbr]

    def lookup_defn(self, defn):
        defn = defn.strip().upper()
        return self.reverse[defn]


def read_file(path, abbrevs):
    with open(path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        abbrevs.add_line(line)


def read_all(dir, abbrevs):
    for filename in os.listdir(dir):
        if filename.endswith(".txt"):
            read_file(os.path.join(dir, filename), abbrevs)


def run_prompt(abbrevs):
    history = pt.history.InMemoryHistory()
    session = pt.PromptSession(history=history, enable_history_search=True)
    print("Hit Ctrl-C or Ctrl-D to exit")
    while True:
        try:
            text = session.prompt("\nlookup > ")
            forward = abbrevs.lookup_abbr(text)
            reverse = abbrevs.lookup_defn(text)
            if forward:
                results = sorted([x.show_defn() for x in forward])
                print((' | '.join(results)))
            if reverse:
                results = sorted([x.show_abbr() for x in reverse])
                for r in results:
                    print(r)
        except (KeyboardInterrupt, EOFError):
            break

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    abbrevs = Abbreviations()
    read_all(data_dir, abbrevs)
    run_prompt(abbrevs)

if __name__ == '__main__':
    main()
