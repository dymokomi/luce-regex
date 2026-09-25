# luce-regex

A small, fast, from-scratch regular-expression engine written in **luce-base**, with two
dialects over one core: the **Oniguruma** subset that TextMate grammars use, and
**ECMAScript** (ES2025 RegExp, with QuickJS's exact syntax, errors and results) for luce-js. It
depends only on the standard library — there is no external regex.

A pattern is parsed by a dialect front end to an AST, compiled once to a flat instruction
array, and matched by an iterative backtracking bytecode VM (the Russ Cox / RE2 / Go design).
The VM is generic over the subject, so each dialect and buffer width gets its own
monomorphised loop; the hot loop is integer comparisons and allocates nothing per step once
its stacks are warm.

The package exports two modules: `regex` (`luce_regex.regex`, the engine) and `libunicode`
(`luce_regex.unicode`, QuickJS's libunicode ported to luce-base: character ranges, case
conversion and folding, normalization, general categories, scripts and binary and sequence
properties; luce-js uses it too).

## The Oniguruma dialect

The subject is an array of Unicode codepoints (`u32`); positions are codepoint indices, so they
line up with how the editor counts offsets. A step budget bounds pathological patterns instead
of hanging.

Supported: literals, `.`, character classes (`[...]`, ranges, negation, `\d \w \s \h` and the
negated forms, a POSIX/`\p` subset), anchors (`^ $ \b \B \A \G \z \Z`), groups (capturing,
`(?:…)`, named `(?<name>…)`), alternation, quantifiers (`* + ? {n} {n,} {n,m}`, greedy and
lazy), backreferences (numeric and named), lookahead and lookbehind, case-insensitive matching,
and the inline flags `(?i) (?x) (?s) (?m)`.

The `Regex` type is exposed to Luce through interop. From Luce:

```luce
let re = regex.compile("\\b(let|var)\\b")
if re.find(line, 0, 0):
    let start = re.match_start()
    let finish = re.match_end()
```

From luce-base, hold a `Regex*` directly and match over a decoded codepoint subject with
`search(subject, offset, anchor)` / `match_at(...)`, reading the result with `match_start()`,
`match_end()`, `group_start(i)`, `group_end(i)` and `group_of(name)`.

## The ECMAScript dialect

Everything ES2025 RegExp has: the flags `d g i m s u v y` (`d` and `g` are only recorded), named
groups (with duplicate names in different alternatives), lookahead and lookbehind with the
specification's backward matching, backreferences (to a group that has not participated they
match empty; `\k<name>`), the quantifier semantics (the empty check and the reset of captures
at each iteration), `\p{...}`/`\P{...}` (General_Category, Script, Script_Extensions, binary
properties, and with `v` the string properties), `v`'s class set operations (nested classes,
`--`, `&&`, `\q{...}`), the modifiers `(?i:...)`/`(?-i:...)`, `\c`, `\x`, `\u{...}`, and the
Annex B extensions allowed without `u` or `v`. Case-insensitive matching uses Canonicalize:
simple case folding with `u` or `v`, toUpperCase otherwise. Syntax errors carry QuickJS's
messages.

Subjects are UTF-16 code units, in an 8-bit (Latin-1) or a 16-bit buffer; positions are code
unit indices. With `u` or `v` a surrogate pair is one code point and a lone surrogate matches
itself; without them everything is code units.

```luce
var message: u8[128]
let re = regex.compile_ecmascript("(?<year>\\d{4})-(?<month>\\d{2})".bytes, regex.es_unicode,
                                  message, none) else trap("syntax error")
defer regex.free_ecmascript(re)
var captures: i32[6]
if regex.exec8(re, "on 2024-05-01".bytes, 0, captures, none) == regex.exec_match:
    # captures: [3, 10, 3, 7, 8, 10] — start and end code unit index of each group, -1 if unset
```

- `compile_ecmascript(pattern, flags, message, host) -> Regex*?` takes the pattern as UTF-8
  bytes with `u`/`v` and as CESU-8 without (each UTF-16 unit encoded alone; lone surrogates
  are three-byte sequences) — what QuickJS's `JS_ToCStringLen2(..., cesu8 = !unicode)` gives.
  `compile_ecmascript16` takes UTF-16 code units and encodes them that way. On a syntax error
  it answers none and writes the message, NUL-terminated, into `message`.
- `capture_count(re)` (including group 0), `program_flags(re)` (the flags plus
  `es_named_groups`), `group_names(re)` (QuickJS's layout: per group after 0, the UTF-8 name, a
  NUL and a scope byte; none without named groups) and `re.group_of(name)` describe it.
- `exec8(re, subject, start, captures, host)` / `exec16(...)` answer `exec_match` (1),
  `exec_no_match` (0), `exec_out_of_memory` (-1) or `exec_interrupted` (-2). Without `y` they
  find the leftmost match at or after `start`; with `y` only one at `start`. `captures` needs
  `2 * capture_count(re)` elements.
- `free_ecmascript(re)` releases the program.
- `parse_escape(text, pos, allow_utf16)` is QuickJS's `lre_parse_escape`, for a JavaScript
  lexer.

`Host` holds the optional callbacks, each receiving `host.opaque` first: `check_stack_overflow`
(asked at each nested disjunction and class while compiling; true fails with "stack overflow"
— matching is iterative and needs no such check), `check_timeout` (polled every 10000 steps
of a match; true makes exec answer -2) and `realloc_func` (C `realloc` semantics; it provides
all of the program's memory, including the backtracking stacks exec grows; C's `realloc` when
absent). The host given to `compile_ecmascript` supplies the allocator for the program's
life; `exec` takes a host for `check_timeout`.

## Tests

`./test.sh` runs the engine's and the Unicode module's tests in native and C comparison modes.
The ECMAScript dialect is checked against upstream QuickJS `libregexp.c`: the conformance
tables of luce-js's libregexp port (`tools/oracle_tables.py`: 413 compile rows, 601 exec rows,
132 escape rows) and more rows printed by `tools/oracle_driver.c` (`tools/oracle_extra.py`:
97 compile and 376 exec rows). Two cases (four rows) differ on purpose, documented in
`es_tests.lucb`: under an allocation failure while building `\d` libregexp reports an empty
message where this engine says "out of memory", and a `v`-flag class string of several
characters inside a lookbehind, which libregexp cannot match, matches here as the
specification requires. `tools/unicode_tables.py` regenerates the Unicode tables.
