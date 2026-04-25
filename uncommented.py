#!/bin/env python3
# This program finds and displays uncommented/undocumented declarations/definitions.
# It's useful for automated tools to block merges of undocumented APIs in header files.

from typing import NamedTuple
import tree_sitter_cpp as tscpp
from argparse import ArgumentParser
from tree_sitter import Language, Node, Parser, Query, QueryCursor, Tree


_cpp_lang = Language(tscpp.language())
_parser = Parser(_cpp_lang)


class UncommentedDeclaration(NamedTuple):
    lineno: int
    source: str


def _query_nodes(tree: Tree, query: str, capture_name: str) -> list[Node]:
    qc = QueryCursor(Query(_cpp_lang, query))
    return [
        c for _, capture in qc.matches(tree.root_node) for c in capture[capture_name]
    ]


def _public_or_protected_members(nodes: list[Node]) -> list[Node]:
    filtered = []
    for node in nodes:
        cur_parent = node.parent
        while cur_parent is not None:
            if cur_parent.type in {
                "class_specifier",
                "struct_specifier",
                "union_specifier",
            }:
                break
            cur_parent = cur_parent.parent
        if cur_parent is None:
            continue
        cur_sibling = node
        while (cur_sibling := cur_sibling.prev_named_sibling) is not None:
            if cur_sibling.type == "access_specifier":
                if cur_sibling.text != b"private":
                    filtered.append(node)
                break
        else:
            if cur_parent.type != "class_specifier":
                filtered.append(node)
    return filtered


def _non_template_definitions(nodes: list[Node]) -> list[Node]:
    filtered = []
    for node in nodes:
        cur_parent = node.parent
        while cur_parent is not None:
            if cur_parent.type == "template_declaration":
                break
            if cur_parent.type in {
                "class_specifier",
                "struct_specifier",
                "union_specifier",
            }:
                cur_parent = None
                break
            cur_parent = cur_parent.parent
        if cur_parent is None:
            filtered.append(node)
    return filtered


def findFunctionDeclarations(tree: Tree) -> list[Node]:
    """
    Finds free function declarations.
    Example: void do_work(int value);
    """
    return _query_nodes(
        tree,
        """
        (translation_unit
            (declaration (function_declarator)) @function.declaration)
        (namespace_definition
          body: (declaration_list
            (declaration (function_declarator)) @function.declaration))
        """,
        "function.declaration",
    )


def findInlineFunctionDefinitions(tree: Tree) -> list[Node]:
    """
    Finds inline free function definitions.
    Example: inline int value() { return 1; }
    """
    return _query_nodes(
        tree,
        '(function_definition (storage_class_specifier "inline")) @function.definition.inline',
        "function.definition.inline",
    )


def findMemberFunctionDeclarations(tree: Tree) -> list[Node]:
    """
    Finds public/protected member function declarations with normal return types.
    Example: class C { public: void method(); };
    """
    return _public_or_protected_members(
        _query_nodes(
            tree,
            """
            (field_declaration
                declarator: (function_declarator
                    declarator: (field_identifier))) @function.member_declaration
            """,
            "function.member_declaration",
        )
    )


def findMemberOperatorDeclarations(tree: Tree) -> list[Node]:
    """
    Finds public/protected member operator declarations.
    Example: class C { public: bool operator==(const C&) const; };
    """
    return _public_or_protected_members(
        _query_nodes(
            tree,
            """
            (field_declaration
                declarator: (function_declarator
                    declarator: (operator_name))) @function.operator_declaration
            (field_declaration
                declarator: (reference_declarator
                    (function_declarator
                        declarator: (operator_name)))) @function.operator_declaration
            """,
            "function.operator_declaration",
        )
    )


def findUserTypeFunctionDeclarations(tree: Tree) -> list[Node]:
    """
    Finds public/protected user-type declarations parsed as declarations.
    Example: class C { public: C(); ~C(); };
    """
    return _public_or_protected_members(
        _query_nodes(
            tree,
            """
            (field_declaration_list
                (declaration (function_declarator)) @function.user_type_declaration)
            """,
            "function.user_type_declaration",
        )
    )


def findMemberFunctionDefinitions(tree: Tree) -> list[Node]:
    """
    Finds public/protected non-operator member function definitions.
    Example: class C { public: C() {} ~C() {} void method() {} };
    """
    return _public_or_protected_members(
        _query_nodes(
            tree,
            """
            (field_declaration_list
                (function_definition
                    declarator: (function_declarator
                        declarator: [(identifier) (destructor_name) (field_identifier)]))
                    @function.member_definition)
            """,
            "function.member_definition",
        )
    )


def findMemberOperatorDefinitions(tree: Tree) -> list[Node]:
    """
    Finds public/protected member operator definitions inside classes.
    Example: class C { public: C& operator=(const C&) { return *this; } };
    """
    return _public_or_protected_members(
        _query_nodes(
            tree,
            """
            (class_specifier
                body: (field_declaration_list
                    (function_definition
                        declarator: (function_declarator
                            declarator: (operator_name))) @function.operator_definition))
            (class_specifier
                body: (field_declaration_list
                    (function_definition
                        declarator: (reference_declarator
                            (function_declarator
                                declarator: (operator_name)))) @function.operator_definition))
            """,
            "function.operator_definition",
        )
    )


def findFreeOperatorDefinitions(tree: Tree) -> list[Node]:
    """
    Finds free operator definitions at translation-unit or namespace scope.
    Example: bool operator==(int a, int b) { return a == b; }
    """
    return _query_nodes(
        tree,
        """
        (translation_unit
            (function_definition
                declarator: (function_declarator
                    declarator: (operator_name))) @function.operator_definition)
        (translation_unit
            (function_definition
                declarator: (reference_declarator
                    (function_declarator
                        declarator: (operator_name)))) @function.operator_definition)
        (namespace_definition
          body: (declaration_list
            (function_definition
                declarator: (function_declarator
                    declarator: (operator_name))) @function.operator_definition))
        (namespace_definition
          body: (declaration_list
            (function_definition
                declarator: (reference_declarator
                    (function_declarator
                        declarator: (operator_name)))) @function.operator_definition))
        """,
        "function.operator_definition",
    )


def findStructFunctionPointerMembers(tree: Tree) -> list[Node]:
    """
    Finds public/protected function pointer members in user types.
    Example: struct Ops { int (*do_it)(int value); };
    """
    return _public_or_protected_members(
        _query_nodes(
            tree,
            """
            (field_declaration
                declarator: (function_declarator
                    declarator: (parenthesized_declarator (pointer_declarator)))) @struct.funcptr_member
            """,
            "struct.funcptr_member",
        )
    )


def findClassDefinitions(tree: Tree) -> list[Node]:
    """
    Finds non-template class definitions.
    Example: class Widget { int value; };
    """
    return _non_template_definitions(
        _query_nodes(
            tree,
            """
            (class_specifier
                name: (type_identifier)
                body: (field_declaration_list)) @class.declaration
            """,
            "class.declaration",
        )
    )


def findStructDefinitions(tree: Tree) -> list[Node]:
    """
    Finds non-template struct definitions.
    Example: struct Data { int value; };
    """
    return _non_template_definitions(
        _query_nodes(
            tree,
            """
            (struct_specifier
                name: (type_identifier)
                body: (field_declaration_list)) @struct.declaration
            """,
            "struct.declaration",
        )
    )


def findUnionDefinitions(tree: Tree) -> list[Node]:
    """
    Finds non-template union definitions.
    Example: union Value { int i; float f; };
    """
    return _non_template_definitions(
        _query_nodes(
            tree,
            """
            (union_specifier
                name: (type_identifier)
                body: (field_declaration_list)) @union.declaration
            """,
            "union.declaration",
        )
    )


def findTemplateClassDefinitions(tree: Tree) -> list[Node]:
    """
    Finds template class definitions.
    Example: template <typename T> class Box { T value; };
    """
    return _query_nodes(
        tree,
        """
        (template_declaration
            (class_specifier
                name: (type_identifier)
                body: (field_declaration_list))) @class.template_declaration
        """,
        "class.template_declaration",
    )


def findTemplateStructDefinitions(tree: Tree) -> list[Node]:
    """
    Finds template struct definitions.
    Example: template <typename T> struct Holder { T value; };
    """
    return _query_nodes(
        tree,
        """
        (template_declaration
            (struct_specifier
                name: (type_identifier)
                body: (field_declaration_list))) @struct.template_declaration
        """,
        "struct.template_declaration",
    )


def findTemplateUnionDefinitions(tree: Tree) -> list[Node]:
    """
    Finds template union definitions.
    Example: template <typename T> union Storage { T value; };
    """
    return _query_nodes(
        tree,
        """
        (template_declaration
            (union_specifier
                name: (type_identifier)
                body: (field_declaration_list))) @union.template_declaration
        """,
        "union.template_declaration",
    )


def findFunctionMacros(tree: Tree) -> list[Node]:
    """
    Finds function-like preprocessor macro definitions.
    Example: #define DOUBLE(x) ((x) * 2)
    """
    return _query_nodes(
        tree,
        "(preproc_function_def) @macro.func_def",
        "macro.func_def",
    )


def find(sourcecode: bytes) -> list[UncommentedDeclaration]:
    """
    Finds uncommented/undocumented declarations.
    Returns a list of undocumented declarations.
    """
    tree = _parser.parse(sourcecode)
    nodes = []
    for finder in (
        findFunctionDeclarations,
        findInlineFunctionDefinitions,
        findMemberFunctionDeclarations,
        findMemberOperatorDeclarations,
        findUserTypeFunctionDeclarations,
        findMemberFunctionDefinitions,
        findMemberOperatorDefinitions,
        findFreeOperatorDefinitions,
        findStructFunctionPointerMembers,
        findClassDefinitions,
        findStructDefinitions,
        findUnionDefinitions,
        findTemplateClassDefinitions,
        findTemplateStructDefinitions,
        findTemplateUnionDefinitions,
        findFunctionMacros,
    ):
        nodes.extend(finder(tree))

    found = []
    for node in sorted(set(nodes), key=lambda n: n.start_byte):
        if has_adjacent_comment(node):
            continue
        assert node.text is not None
        found.append(
            UncommentedDeclaration(node.start_point.row + 1, node.text.decode())
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
        print(hooligan.lineno, ": ", hooligan.source.split("\n")[0], sep="")


if __name__ == "__main__":
    main()
