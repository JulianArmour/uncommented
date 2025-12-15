import unittest
import uncommented


class FunctionDeclarations(unittest.TestCase):
    def test_without_any_docs(self):
        src = """\
        void function_without_any_docs();
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("function_without_any_docs", found[0].source)

    def test_missing_adjacent_docs(self):
        src = """\
        //I'm not adjacent!

        void function_missing_adjacent_docs();
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("function_missing_adjacent_docs", found[0].source)

    def test_with_docs_inline(self):
        src = """\
        void function_with_docs_inline(); // This is bad style, so this is "undocumented".
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("function_with_docs_inline", found[0].source)

    def test_typical_trippleslash_multiline_comment(self):
        src = """\
        ///Hi I am on the first line...
        ///Hi I am on the second line!
        void typical_trippleslash_multiline_comment(int *arg1, int arg2);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_typical_trippleslash_singleline_comment(self):
        src = """\
        /// this is my documentation!
        void typical_trippleslash_singleline_comment(int *arg1, int arg2);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_typical_doubleslash_singleline_comment(self):
        src = """\
        //docs for this functions
        int typical_doubleslash_singleline_comment(char *a);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_typical_slashstar_singleline_comment(self):
        src = """\
        /*There are two stars in this comment.*/
        int typical_slashstar_singleline_comment(char *a);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_typical_slashstarstar_multiline_comment(self):
        src = """\
        /**
        * docs for this function!
        */
        int typical_slashstarstar_multiline_comment(char *a);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)


class InlineFunctionDefinitions(unittest.TestCase):
    def test_undocumented(self):
        src = """\
        inline void inline_function_without_docs() {}
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("inline_function_without_docs", found[0].source)

    def test_non_adjacent_documentation(self):
        src = """\
        /// This is not adjacent

        inline void inline_function_with_non_adjacent_docs() {}
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("inline_function_with_non_adjacent_docs", found[0].source)

    def test_documented_trippleslash(self):
        src = """\
        /// This is documented
        inline void inline_function_with_docs() {}
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_documented_starstar(self):
        src = """\
        /**
        * docs for this inline function!
        */
        inline int typical_slashstarstar_multiline_comment_inline_def(char *a) { return 0; }
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)


class PreprocMacroFunctions(unittest.TestCase):
    def test_undocumented(self):
        src = """\
        #define MY_FUNC(x) ((x) * 2)
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("MY_FUNC", found[0].source)

    def test_documented_starstar(self):
        src = """\
        /** This function macro does the thing!*/
        #define MY_MACRO_FUNC(x) ((x) * 2)
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)


class StructFunctionPointerMembers(unittest.TestCase):
    def test_undocumented_function_pointer_member(self):
        src = """\
        /// docs for Ops
        struct Ops {
            int (*do_it)(int a);
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("do_it", found[0].source)

    def test_documented_function_pointer_member_with_line_comment(self):
        src = """\
        /// docs for Ops
        struct Ops {
            /// docs for do_it
            int (*do_it)(int a);
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_documented_function_pointer_member_with_block_comment(self):
        src = """\
        /// docs for Ops
        struct Ops {
            /**
             * docs for cb
             */
            void (*cb)(void);
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_ignores_non_function_pointer_fields(self):
        src = """\
        /// docs for Ops
        struct Ops {
            int count;
            int (*do_it)(int a);
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("do_it", found[0].source)


class CppClassDeclarations(unittest.TestCase):
    def test_undocumented_class_definition(self):
        src = """\
        class MyClass {};
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("MyClass", found[0].source)

    def test_documented_class_definition(self):
        src = """\
        /// docs for MyClass
        class MyClass {};
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_class_forward_declaration(self):
        """
        Forward Decls are OK. We just care about the definitions.
        Let's assert that.
        """
        src = """\
        class ForwardDecl;
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_union_definitions(self):
        src = """\
        union Value { int i; float f; };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)

    def test_union_definitions(self):
        src = """\
        // Docs for Value
        union Value { int i; float f; };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_struct_definitions(self):
        src = """\
        struct Data { int x; };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("Data", found[0].source)

    def test_struct_definitions(self):
        src = """\
        /**
        * docs for Data
        */
        struct Data { int x; };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_template_class_forward_declaration(self):
        src = """\
        template <typename T>
        class Box;
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_template_class_definition(self):
        src = """\
        template <typename T>
        class Box {};
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("Box", found[0].source)

    def test_documented_template_class_definition(self):
        src = """\
        /// docs for Box
        template <typename T>
        class Box {};
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_anonymous_struct_not_reported(self):
        src = """\
        struct {
            int x;
        } anon;
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_friend_class_declaration_is_skipped(self):
        src = """\
        /// docs for Owner
        class Owner {
        public:
            friend class Pal;
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)


class CppClassMembers(unittest.TestCase):
    # Decision: allow undocumented private members. Since I only care about the public API.

    def test_undocumented_public_method_decl(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        public:
            void undocumented_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("undocumented_method", found[0].source)

    def test_undocumented_private_member_function_decl(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        private:
            void undocumented_private_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_public_and_private_method_decl(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        public:
            void undocumented_public_method();
        private:
            void undocumented_private_method();
        public:
            void another_undocumented_public_method();
        private:
            void another_undocumented_private_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 2)
        self.assertIn("undocumented_public_method", found[0].source)
        self.assertIn("another_undocumented_public_method", found[1].source)

    def test_documented_public_method_decl(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        public:
            /// This is documented
            void documented_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_protected_method_decl(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        protected:
            void undocumented_protected_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("undocumented_protected_method", found[0].source)

    def test_documented_protected_method_decl(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        protected:
            /// This is documented
            void documented_protected_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_public_and_protected_method_decls(self):
        src = """\
        /// docs for MyClass
        class MyClass {
        public:
            void undocumented_public_method();
        protected:
            void undocumented_protected_method();
        public:
            void another_undocumented_public_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 3)
        self.assertIn("undocumented_public_method", found[0].source)
        self.assertIn("undocumented_protected_method", found[1].source)
        self.assertIn("another_undocumented_public_method", found[2].source)


if __name__ == "__main__":
    unittest.main()
