from aggregator import aggregator

def iter_files(line_iterable):
    for file_diff in aggregator(line_parser.parse_lines(line_iterable)):
        yield file_diff
