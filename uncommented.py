#!/bin/env python3
# This program finds and displays uncommented/undocumented function declarations.
# It's useful for automated tools to block merges of undocumented APIs in header files.

import tree_sitter_cpp as tscpp
from argparse import ArgumentParser
from tree_sitter import Language, Parser, Query, QueryCursor
from pprint import pprint

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
        """
        (
          (comment)* @function.documentation
          .
          (declaration
            (function_declarator
                (identifier) @function.identifier
            )
          ) @function.declaration
        )
        """
    )

    # Lets go through each function declaration and associate identifier -> list(comment_line).
    # Documentation comments are always adjacent to another doc comment, or the function declaration.
    # We need to filter out those comments which are *not* adjacent.
    identifier_comment = {}
    qc = QueryCursor(query)
    for matches in qc.matches(tree.root_node):
        _, captures = matches
        identifier_node = captures["function.identifier"][0]
        assert identifier_node.text is not None
        identifier = identifier_node.text.decode()
        func_decl = captures["function.declaration"][0]
        decl_start_line = func_decl.start_point[0]
        # go through each comment (bottom->up) to see if it is adjacent
        # keep in mind, some functions may be undocumented.
        comments = []
        for offset, comment in enumerate(reversed(captures.get("function.documentation", [])), 1):
            if comment.start_point[0] == decl_start_line - offset:
                assert comment.text is not None
                comments.append(comment.text.decode())
        identifier_comment[identifier] = list(reversed(comments))
        assert func_decl.text is not None
        if len(comments) == 0:
            print(func_decl.start_point[0], ": ", func_decl.text.decode().replace("\n", ""), sep="")


if __name__ == "__main__":
    main()

