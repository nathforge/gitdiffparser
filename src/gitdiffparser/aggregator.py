import line_parser

def aggregator(parsed_lines_iterable):
    def set_once(root, path, value):
        original_path = list(path)

        path = list(path)
        last_key = path.pop()

        for key in path:
            root = root[key]

        if last_key in root:
            raise KeyError("{!r} is already set".format(original_path))

        root[last_key] = value

    file_diff = None
    file_meta = None
    chunk_diff = None
    chunk_meta = None
    for state, parsed, _ in parsed_lines_iterable:
        if state == "file_diff_header":
            if file_diff is not None:
                yield file_diff
                file_diff = None
                file_meta = None
                chunk_diff = None
                chunk_meta = None

            file_diff = {}
            file_meta = {"no_newline_count": 0}
            set_once(file_diff, ("from",), {})
            set_once(file_diff, ("from", "file",), parsed["from_file"])
            set_once(file_diff, ("from", "end_newline",), True)
            set_once(file_diff, ("to",), {})
            set_once(file_diff, ("to", "file",), parsed["to_file"])
            set_once(file_diff, ("to", "end_newline",), True)
            set_once(file_diff, ("is_binary",), False)
            set_once(file_diff, ("chunks",),    [])
            continue

        if state == "new_file_mode_header":
            set_once(file_diff, ("from", "mode",), "0000000")
            set_once(file_diff, ("to",   "mode",), parsed["mode"])
            continue

        if state == "old_mode_header":
            set_once(file_diff, ("from", "mode",), parsed["mode"])
            continue

        if state == "new_mode_header":
            set_once(file_diff, ("to", "mode",), parsed["mode"])
            continue

        if state == "deleted_file_mode_header":
            set_once(file_diff, ("from", "mode",), parsed["mode"])
            set_once(file_diff, ("to",   "mode",), "0000000")
            continue

        if state in ("a_file_change_header", "b_file_change_header"):
            key = {"a_file_change_header": "from", "b_file_change_header": "to"}[state]
            if file_diff[key]["file"] != parsed["file"] and parsed["file"] is not None:
                print file_diff, parsed
                raise Exception("TODO: Exception text")
            continue

        if state == "binary_diff":
            file_diff["is_binary"] = True
            continue

        if state == "index_diff_header":
            set_once(file_diff, ("from", "blob",), parsed["from_blob"])
            set_once(file_diff, ("to", "blob",), parsed["to_blob"])
            if parsed["mode"] is not None:
                set_once(file_diff, ("from", "mode",), parsed["mode"])
                set_once(file_diff, ("to", "mode"), parsed["mode"])
            continue

        if state == "chunk_header":
            chunk_meta = {
                "from_line_number": parsed["from_line_start"],
                "to_line_number":   parsed["to_line_start"]
            }
            chunk_diff = {}
            set_once(chunk_diff, ("lines",), [])
            set_once(chunk_diff, ("from",), {})
            set_once(chunk_diff, ("from", "line_start"), parsed["from_line_start"])
            set_once(chunk_diff, ("from", "line_count"), parsed["from_line_count"])
            set_once(chunk_diff, ("to",), {})
            set_once(chunk_diff, ("to", "line_start"), parsed["to_line_start"])
            set_once(chunk_diff, ("to", "line_count"), parsed["to_line_count"])
            file_diff["chunks"].append(chunk_diff)
            continue

        if state == "line_diff":
            chunk_diff["lines"].append({
                "from_line_number": chunk_meta["from_line_number"],
                "to_line_number": chunk_meta["to_line_number"],
                "line": parsed["line"],
                "action": {
                    "-": "delete",
                    "+": "add",
                    " ": "context"
                }[parsed["action"]]
            })

            if parsed["action"] in (" ", "-"):
                chunk_meta["from_line_number"] += 1
            if parsed["action"] in (" ", "+"):
                chunk_meta["to_line_number"] += 1

            if file_meta["no_newline_count"] > 0:
                file_diff["to"]["end_newline"] = True
                file_diff["from"]["end_newline"] = False

            continue

        if state == "no_newline":
            file_meta["no_newline_count"] += 1
            if file_meta["no_newline_count"] > 2:
                raise Exception("TODO: Exception text")
            file_diff["to"]["end_newline"] = False
            continue

        raise Exception("Unexpected {!r} line".format(state))

    if file_diff is not None:
        yield file_diff
