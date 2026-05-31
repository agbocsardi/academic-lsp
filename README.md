# academic-lsp

Experimental language server diagnostics for academic prose.

Inspired by Martin Kleppmann's Bluesky post asking for IDE-style red squiggles when prose refers to a non-obvious concept before defining it:

<https://bsky.app/profile/martin.kleppmann.com/post/3mn5fqwajvs2l>

## Lore

One of the professors at Gergő's school says that "academic writing is more code than literature" because it has to be structured immensely. This project takes that seriously: if prose has code-like structure, it should be possible to build code-like diagnostics for it.

## Goal

Bring code-editor feedback loops to academic writing:

- warn when an abbreviation is used before it is defined
- warn when a potentially technical concept appears before a local definition
- eventually warn when adjacent paragraphs do not connect cleanly

The first scaffold is intentionally small and deterministic. LLM-backed semantic diagnostics can come later once the editor/server loop is solid.

## Current prototype

The server currently emits diagnostics for common abbreviation patterns:

- `LSP` used without a nearby earlier definition like `Language Server Protocol (LSP)`
- abbreviation definitions are collected from the current document
- diagnostics update through normal LSP `textDocument/didOpen` and `textDocument/didChange` events

## Install for local development

```bash
uv sync
uv run academic-lsp --help
```

## Configuration

The server is meant to be configured per project. Copy `academic-lsp.example.toml` to `academic-lsp.toml` and adjust it.

```toml
[rules]
files = [
  ".academic-lsp/rules/base.md",
  ".academic-lsp/rules/discipline.md",
  ".academic-lsp/rules/supervisor.md",
]

[llm]
provider = "openai-compatible"
base_url = "https://your-endpoint.example/v1"
model = "deepseek-v4-flash"
temperature = 0.0
api_key_env = "ACADEMIC_LSP_API_KEY"
```

API keys should live in environment variables, not in the project config.

Diagnostic triggers are configurable. Defaults are intentionally conservative:

- deterministic checks run on idle by default
- LLM-backed checks run on save by default
- expensive checks should also support manual runs later

```toml
[diagnostics.abbreviations]
enabled = true
engine = "deterministic"
run_on = "idle"
debounce_ms = 1500

[diagnostics.paragraph_transitions]
enabled = true
engine = "llm"
run_on = "save"
```

This keeps typing responsive while still letting heavier semantic checks run when the draft reaches a stable point.

## Rule files

Rule files are plain Markdown so different disciplines, journals, supervisors, or writing courses can bring their own standards.

```md
# Rules

## Abbreviations

- Define abbreviations on first use.
- Do not abbreviate terms used fewer than three times.

## Paragraphs

- Each paragraph should have a clear topic sentence.
- The first sentence should connect to the previous paragraph.
```

Diagnostics should cite the rule that triggered them where possible, so warnings feel like configured writing standards rather than generic AI opinions.

## Neovim sketch

This can be registered as a custom LSP server:

```lua
vim.api.nvim_create_autocmd({ "BufReadPost", "BufNewFile" }, {
  pattern = { "*.md", "*.qmd", "*.tex" },
  callback = function()
    vim.lsp.start({
      name = "academic-lsp",
      cmd = { "uv", "run", "academic-lsp" },
      root_dir = vim.fs.root(0, { ".git" }) or vim.fn.getcwd(),
    })
  end,
})
```

## Direction

Possible diagnostic layers:

1. deterministic abbreviation checks
2. noun-phrase/concept extraction with local definition tracking
3. paragraph transition/coherence checks
4. optional small local model pass for fuzzy academic-prose warnings

The design target is not autocomplete or rewriting. It is quiet, local, editor-native feedback while drafting.
