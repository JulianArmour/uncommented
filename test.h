/// Expand the file names in the global argument list.
/// If "fnum_list" is not NULL, use "fnum_list[fnum_len]" as a list of buffer
/// numbers to be re-used.
void
alist_expand(int *fnum_list, int fnum_len);

//docs for foo
int foo(char *a);

void bar();


//I'm not adjacent!

void missing_adjacent_comment();

/// This flag is set whenever the argument list is being changed and calling a

/// function that might trigger an autocommand.
static bool arglist_locked = false;
