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
