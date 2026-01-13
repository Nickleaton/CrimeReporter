from enum import Enum
from pathlib import Path

import yaml


class Offence:

    def __init__(self, name: str, sentence: str):
        self.name = name
        self.sentence = sentence

    def to_dict(self):
        return {"name": self.name, "sentence": self.sentence}


class Role(Enum):
    Unknown = 0
    Offender = 1
    Victim = 2
    Police = 3
    Judge = 4


class Person:

    def __init__(self, name):
        self.name = name
        self.age = 0
        self.dob = ""
        self.ancestry_link = ""
        self.offences = []
        self.type = Role.Unknown

    def to_dict(self):
        return {
            "name": self.name,
            "age": self.age,
            "dob": self.dob,
            "ancestry_link": self.ancestry_link,
            "offences": [o.to_dict() for o in self.offences],
        }


class People:
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.people = []

        if self.filepath.exists():
            with self.filepath.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or []

            for item in data:
                person = Person(item.get("name"))
                person.age = item.get("age")
                person.dob = item.get("dob")
                person.ancestry_link = item.get("ancestry_link")
                self.people.append(person)

    def add_person(self, person: Person):
        """Add a Person instance to the collection."""
        self.people.append(person)

    def to_dict(self):
        return [p.to_dict() for p in self.people]

    def save(self):
        """Save all people to the YAML file."""
        with self.filepath.open("w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, sort_keys=False)
