from __future__ import annotations

import re


SOLUTION_HEADINGS = re.compile(r"(?im)^\s{0,3}#{0,6}\s*(?:intended solution|analysis and suggested fix|suggested fix|proposed fix|solution|how to fix|repair instructions)\s*:?.*$")


def solution_sections(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if SOLUTION_HEADINGS.match(line)]
    sections: list[str] = []
    for start in starts:
        end = len(lines)
        for index in range(start + 1, len(lines)):
            if re.match(r"^\s{0,3}#{1,6}\s+", lines[index]):
                end = index
                break
        sections.append("\n".join(lines[start:end]))
    return sections
