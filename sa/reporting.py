from __future__ import print_function

def format_metric_row(metric, classification, tool, score, status):
    return {'metric': metric, 'classification': classification, 'tool': tool, 'score': score, 'status': status}
def render_text_report(rows):
    lines = ['Structural Analysis Report']
    for row in rows:
        lines.append('%(metric)s tool=%(tool)s score=%(score)s' % row)
    return '\n'.join(lines)
