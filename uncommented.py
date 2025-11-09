#!/bin/env python3
# This program finds and displays uncommented/undocumented function declarations.
# It's useful for automated tools to block merges of undocumented APIs in header files.

from typing import NamedTuple
import tree_sitter_cpp as tscpp
from argparse import ArgumentParser
from tree_sitter import Language, Parser, Query, QueryCursor


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
        _, nodes = next(iter(captures.items()))
        func_decl = nodes[0]  # there can only be one
        previous_node = func_decl.prev_named_sibling
        if (
            previous_node is None
            or previous_node.type != "comment"
            or previous_node.end_point.row + 1 != func_decl.start_point.row
        ):
            assert func_decl.text is not None
            found.append(
                UncommentedDeclaration(
                    func_decl.start_point.row, func_decl.text.decode()
                )
            )
    return found


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
