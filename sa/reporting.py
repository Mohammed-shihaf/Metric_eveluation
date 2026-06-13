from __future__ import print_function

class MetricReportBuilder(object):
    """Format analysis summaries for console or gate export."""

    def __init__(self, title):
        self.title = title
        self.sections = []

    def add_section(self, name, rows):
        self.sections.append((name, list(rows)))

    def render_text(self):
        lines = [self.title, '=' * len(self.title)]
        for name, rows in self.sections:
            lines.append('')
            lines.append(name)
            lines.append('-' * len(name))
            for row in rows:
                lines.append('  %s' % row)
        return '\n'.join(lines)

    def section_count(self):
        return len(self.sections)

    def row_count(self):
        total = 0
        for _, rows in self.sections:
            total += len(rows)
        return total
