( Trivial program that retrieves all the posts on a CorkBoard.
  Thanks Kelketek for doing the work to make this trivial.

  Expects the name of a matchable board reading command on
  the stack when it starts.
)
( Some strings to help an external bot use this program. )
$def START_STRING "--- START"
$def END_STRING "--- END"
$def ERROR_STRING "--- ERROR: "

$def CORKBOARD_REF #21810

: error ( s -- )
    ERROR_STRING swap strcat me @ swap notify
;

: main ( s -- s )
    me @ START_STRING notify

    ( Sanity check the input )
    dup "" strcmp 0 = if
        "Requires the name of a board command. e.g. '+read'" error
        exit
    then
    match  ( match the provided command )
    dup int 0 < if
        "Command not found or ambiguous." error
        exit
    then

    ( Now process and display the board contents )
    CORKBOARD_REF "get-all-CorkBoard-posts" call
    ( Go through the array of posts and process each one, constructing a new list. )
    ( Sample item:  4{"content":1{...} "owner":#3183 "postID":"1494311622" "title":"Initial commit"} )
    { swap
    foreach
        ( We don't care about the index: drop it. )
        swap pop
        ( Replace the array 'content' with one long string. )
        ( TODO: Revisit this if we run into space issues.)
        dup "content" array_getitem array_count swap "content_len" array_insertitem
        dup "content" array_getitem "\r|" array_join
        swap "content" array_insertitem
    repeat
    }list
    {
        "|owner: %[owner]d\r"
        "|time: %[postID]s\r"
        "|title: %[title]s\r"
        "|length: %[content_len]i\r"
        "|content:\r"
        "|%[content]s"
    }join
    array_fmtstrings
    foreach
        me @ swap notify
    repeat
    me @ END_STRING notify
;
