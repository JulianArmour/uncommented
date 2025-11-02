#!/bin/env python3
# This program finds and displays uncommented/undocumented function declarations.
# It's useful for automated tools to block merges of undocumented APIs in header files.

import tree_sitter_cpp as tscpp
from argparse import ArgumentParser
from tree_sitter import Language, Parser, Query, QueryCursor

def main():
    argParser = ArgumentParser(description="Find and display commented/uncommented function declarations")
    argParser.add_argument("file", help="Path to the file to analyze.")
    args = argParser.parse_args()


    with open(args.file, "rb") as f:
        file_b = f.read()

    cpp_lang = Language(tscpp.language())
    parser = Parser(cpp_lang)
    tree = parser.parse(file_b)
    query = Query(
        cpp_lang,
        "(declaration (function_declarator)) @function.declaration"
    )

    qc = QueryCursor(query)
    for matches in qc.matches(tree.root_node):
        _, captures = matches
        func_decl = captures["function.declaration"][0]
        previous_node = func_decl.prev_named_sibling
        if (previous_node is None
            or previous_node.type != "comment"
            or previous_node.start_point[0] + 1 != func_decl.start_point[0]
        ):
            assert func_decl.text is not None
            print(func_decl.start_point[0], ": ", func_decl.text.decode().replace("\n", ""), sep="")


if __name__ == "__main__":
    main()

