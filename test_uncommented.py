import unittest
import uncommented

class TestUncommented(unittest.TestCase):
    SAMPLE_SRC = """\
    ///Hi I am on the first line...
    ///Hi I am on the second line!
    void typical_trippleslash_multiline_comment(int *arg1, int arg2);


    /// this is my documentation!
    void typical_trippleslash_singleline_comment(int *arg1, int arg2);


    //docs for foo
    int typical_doubleslash_singleline_comment(char *a);


    /*There are two stars in this comment.*/
    int typical_slashstar_singleline_comment(char *a);


    /**
    * docs for foo
    */
    int typical_slashstarstar_multiline_comment(char *a);


    void function_without_any_docs();


    //I'm not adjacent!

    void function_missing_adjacent_docs();


    void function_with_docs_inline(); // This is bad style, so this is undocumented.
    """

    def test_find(self):
        must_be_found = {
            "function_without_any_docs",
            "function_missing_adjacent_docs",
            "function_with_docs_inline",
        }
        found = uncommented.find(TestUncommented.SAMPLE_SRC.encode())
        what_be_found = set(
            func for decl in found
                 for func in must_be_found
                 if func in decl.source
        )
        self.assertSetEqual(what_be_found, must_be_found)
        self.assertEqual(len(found), len(must_be_found))


if __name__ == '__main__':
    unittest.main()
