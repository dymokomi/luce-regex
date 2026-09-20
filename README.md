# luce-regex

A small, fast, from-scratch regular-expression engine written in **luce-base**, covering the
Oniguruma subset that TextMate grammars use. It depends only on the standard library — there is
no external regex.

A pattern is parsed to an AST, compiled once to a flat instruction array, and matched by an
iterative backtracking bytecode VM (the Russ Cox / RE2 / Go design). The subject is an array of
Unicode codepoints (`u32`); positions are codepoint indices, so they line up with how the editor
counts offsets. The hot loop is integer comparisons and allocates nothing per step. A step
budget bounds pathological patterns instead of hanging.

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
