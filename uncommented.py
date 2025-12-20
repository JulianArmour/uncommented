#!/bin/env python3
# This program finds and displays uncommented/undocumented declarations/definitions.
# It's useful for automated tools to block merges of undocumented APIs in header files.

from typing import NamedTuple, Tuple
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

    (field_declaration
        declarator: (function_declarator
            declarator: (field_identifier))) @function.member_declaration

    (field_declaration
        declarator: (function_declarator
            declarator: (operator_name))) @function.operator_declaration
    (field_declaration
        declarator: (reference_declarator
            (function_declarator
                declarator: (operator_name)))) @function.refoperator_declaration

    (class_specifier
        body: (field_declaration_list
            (function_definition
                declarator: (function_declarator
                    declarator: [(identifier)(destructor_name)])) @function.con_des_structor_definition))

    (function_definition
        declarator: (function_declarator
            declarator: (operator_name))) @function.operator_definition

    (function_definition
        declarator: (reference_declarator
            (function_declarator
                declarator: (operator_name)))) @function.refoperator_definition

    (field_declaration
        declarator: (function_declarator
            declarator: (parenthesized_declarator (pointer_declarator)))) @struct.funcptr_member

    (class_specifier
        name: (type_identifier)
        body: (field_declaration_list)) @class.declaration

    (struct_specifier
        name: (type_identifier)
        body: (field_declaration_list)) @struct.declaration

    (union_specifier
        name: (type_identifier)
        body: (field_declaration_list)) @union.declaration

    (template_declaration
        (class_specifier
            name: (type_identifier)
            body: (field_declaration_list))) @class.template_declaration

    (template_declaration
        (struct_specifier
            name: (type_identifier)
            body: (field_declaration_list))) @struct.template_declaration

    (template_declaration
        (union_specifier
            name: (type_identifier)
            body: (field_declaration_list))) @union.template_declaration

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
        if not has_adjacent_comment(node_of_interest):
            assert node_of_interest.text is not None
            found.append(
                UncommentedDeclaration(
                    node_of_interest.start_point.row, node_of_interest.text.decode()
                )
            )
    return found


def has_adjacent_comment(node: Node) -> bool:
    """
    Returns True when an adjacent comment documents the node.
    Handles typedef struct/union/class definitions where the comment precedes
    the typedef, not the struct/union/class specifier itself.
    """
    previous_node = node.prev_named_sibling
    if (
        previous_node is not None
        and previous_node.type == "comment"
        and previous_node.end_point.row + 1 == node.start_point.row
    ):
        return True
    # deal with typedefs
    parent = node.parent
    if parent is None or parent.type != "type_definition":
        return False
    parent_prev_node = parent.prev_named_sibling
    return (
        parent_prev_node is not None
        and parent_prev_node.type == "comment"
        and parent_prev_node.end_point.row + 1 == parent.start_point.row
    )


def skip_this_node(capture_name: str, node: Node) -> bool:
    """
    Tree-sitter queries are powerful but cannot handle all situations. This function
    applies ad-hoc checks to captured nodes to indicate if we don't care about this node.
    This keeps the queries very simple. Useful for annoying C++ parsing.
    """
    class_like_caps = {
        "class.declaration",
        "struct.declaration",
        "union.declaration",
    }
    if capture_name in class_like_caps:
        cur_node = node
        while cur_node is not None:
            if cur_node.type == "template_declaration":
                return True  # Templates have their own capture
            cur_node = cur_node.parent

    # skip private members
    it_is, the_type = is_in_user_type(node)
    if it_is:
        cur_node = node
        while (cur_node := cur_node.prev_named_sibling) is not None:
            if cur_node.type == "access_specifier":
                return cur_node.text == b"private"
        return the_type == "class_specifier"  # class members are private by default

    return False


def is_in_user_type(node: Node) -> Tuple[bool, str]:
    cur_node = node.parent
    while cur_node is not None:
        if cur_node.type in {"class_specifier", "struct_specifier", "union_specifier"}:
            return True, cur_node.type
        cur_node = cur_node.parent
    return False, ""


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
