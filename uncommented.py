#!/bin/env python3
# This program finds and displays uncommented/undocumented function declarations.
# It's useful for automated tools to block merges of undocumented APIs in header files.

from typing import NamedTuple
import tree_sitter_cpp as tscpp
from argparse import ArgumentParser
from tree_sitter import Language, Node, Parser, Query, QueryCursor


_cpp_lang = Language(tscpp.language())
_parser = Parser(_cpp_lang)
_query = Query(
    _cpp_lang,
    """\
    (declaration (function_declarator)) @function.declaration

    (function_definition (storage_class_specifier "inline")) @function.definition.inline

    (field_declaration (function_declarator)) @function.member_declaration

    (preproc_function_def) @macro.func_def
    """,
)


class UncommentedDeclaration(NamedTuple):
    lineno: int
    source: str


def find(sourcecode: bytes) -> list[UncommentedDeclaration]:
    """
    Finds uncommented/undocumented function declarations.
    Returns a list of undocumented declarations
    """
    tree = _parser.parse(sourcecode)
    found = []
    qc = QueryCursor(_query)
    for matches in qc.matches(tree.root_node):
        _, captures = matches
        assert len(captures) == 1, "Only 1 capture per pattern is supported."
        cap_name, nodes = next(iter(captures.items()))
        node_of_interest = nodes[0]  # there can only be one
        if skip_this_node(cap_name, node_of_interest):
            continue
        previous_node = node_of_interest.prev_named_sibling
        if (
            previous_node is None
            or previous_node.type != "comment"
            or previous_node.end_point.row + 1 != node_of_interest.start_point.row
        ):
            assert node_of_interest.text is not None
            found.append(
                UncommentedDeclaration(
                    node_of_interest.start_point.row, node_of_interest.text.decode()
                )
            )
    return found


def skip_this_node(capture_name: str, node: Node) -> bool:
    """
    Tree-sitter queries are powerful but cannot handle all situations. This function
    applies ad-hoc checks to captured nodes to indicate if we don't care about this node.
    This keeps the queries very simple. Useful for annoying C++ parsing.
    """
    # only handle public members in classes
    if capture_name == "function.member_declaration":
        cur_node = node
        while (cur_node := cur_node.prev_named_sibling) is not None:
            if cur_node.type == "access_specifier":
                return cur_node.text == b"private"
        return True  # class members are private by default

    return False


def main():
    argParser = ArgumentParser(
        description="Find and display commented/uncommented function declarations"
    )
    argParser.add_argument("file", help="Path to the file to analyze.")
    args = argParser.parse_args()

    with open(args.file, "rb") as f:
        file_b = f.read()

    hooligans = find(file_b)
    for hooligan in hooligans:
        print(hooligan.lineno, ": ", hooligan.source.replace("\n", ""), sep="")


if __name__ == "__main__":
    main()
