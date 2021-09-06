import collections
import os

import prompt_toolkit as pt


class Abbreviations:
    def __init__(self):
        self.abbrevs = collections.defaultdict(set)

    def add(self, abbr, defn):
        """Add an abbreviation and definition pair."""
        if " "  in abbr:
            # An abbreviation with an explanation, e.g.
            #   MO (medical officer): Doctor
            # Strip off the explanationn and add it to the definition side.
            abbr, expl = abbr.split(" ", 1)
            defn = defn + " " + expl
        self.abbrevs[abbr.upper()].add(defn)

    def add_line(self, line):
        """Add a line read from a data file."""
        line = line.strip()
        if line.startswith("#") or line == "":
          return
        if "->" in line:
            l, r = line.split(" -> ")
            abbrevs = [x.strip() for x in r.split(",")]
            for a in abbrevs:
                self.add(a, l)
        elif ":" in line:
            l, r = line.split(":", 1)
            self.add(l, r)
        else:
            raise ValueError(f"Could not parse line: {line}")

    def lookup(self, abbr):
        return self.abbrevs[abbr]


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
            abbr = text.strip().upper()
            results = sorted([x.strip() for x in abbrevs.lookup(abbr)])
            print((' | '.join(results)))
        except (KeyboardInterrupt, EOFError):
            break

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    abbrevs = Abbreviations()
    read_all(data_dir, abbrevs)
    run_prompt(abbrevs)

if __name__ == '__main__':
    main()
