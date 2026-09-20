# luce-regex

A small, from-scratch regular-expression engine for Luce, covering the Oniguruma subset that
TextMate grammars use. It depends only on the standard library — there is no external regex.

It compiles a pattern to an AST and matches by backtracking. The subject is a sequence of
Unicode scalars (one-scalar strings), matched with scalar-value order, so it lines up with how
the editor counts offsets. A step budget bounds pathological patterns instead of hanging.

Supported: literals, `.`, character classes (`[...]`, ranges, negation, `\d \w \s` and the
negated forms, a POSIX subset), anchors (`^ $ \b \B \A \G \z \Z`), groups (capturing,
`(?:…)`, named `(?<name>…)`), alternation, quantifiers (`* + ? {n} {n,} {n,m}`, greedy and
lazy), backreferences (numeric and named), lookahead and lookbehind, case-insensitive matching,
and the inline flags `(?i) (?x) (?s) (?m)`.

```luce
from regex import Regex
let re = Regex("\\b(let|var)\\b")
if let m = re.search(scalars, 0, 0):
    ...
```
