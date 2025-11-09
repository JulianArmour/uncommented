import unittest
import uncommented


class TestUncommentedFuncDeclPositive(unittest.TestCase):
    """Tests for uncommented.find function to find undocumented function declarations."""

    def test_find_function_without_any_docs(self):
        src = """\
        void function_without_any_docs();
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("function_without_any_docs", found[0].source)

    def test_find_function_missing_adjacent_docs(self):
        src = """\
        //I'm not adjacent!

        void function_missing_adjacent_docs();
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("function_missing_adjacent_docs", found[0].source)

    def test_find_function_with_docs_inline(self):
        src = """\
        void function_with_docs_inline(); // This is bad style, so this is undocumented.
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 1)
        self.assertIn("function_with_docs_inline", found[0].source)


class TestUncommentedFuncDeclNegative(unittest.TestCase):
    """Tests for uncommented.find function to ensure documented function declarations are not found."""

    def test_find_typical_trippleslash_multiline_comment(self):
        src = """\
        ///Hi I am on the first line...
        ///Hi I am on the second line!
        void typical_trippleslash_multiline_comment(int *arg1, int arg2);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_find_typical_trippleslash_singleline_comment(self):
        src = """\
        /// this is my documentation!
        void typical_trippleslash_singleline_comment(int *arg1, int arg2);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_find_typical_doubleslash_singleline_comment(self):
        src = """\
        //docs for this functions
        int typical_doubleslash_singleline_comment(char *a);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_find_typical_slashstar_singleline_comment(self):
        src = """\
        /*There are two stars in this comment.*/
        int typical_slashstar_singleline_comment(char *a);
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_find_typical_slashstarstar_multiline_comment(self):
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


class CppClassMembers(unittest.TestCase):
    # Decision: allow undocumented private members. Since I only care about the public API.

    def test_undocumented_public_method_decl(self):
        src = """\
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
        class MyClass {
        private:
            void undocumented_private_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)

    def test_undocumented_public_and_private_method_decl(self):
        src = """\
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
        class MyClass {
        public:
            /// This is documented
            void documented_method();
        };
        """
        found = uncommented.find(src.encode())
        self.assertEqual(len(found), 0)


if __name__ == "__main__":
    unittest.main()
