#!/usr/bin/env bash
set -euo pipefail

tmpdir=$(mktemp -d)
mkdir -p "$tmpdir/config/nvim" "$tmpdir/data" "$tmpdir/state" "$tmpdir/cache"

cat > "$tmpdir/test.md" <<'MD'
This paper uses LSP diagnostics for prose.
MD

cat > "$tmpdir/config/nvim/init.lua" <<'LUA'
vim.diagnostic.config({ virtual_text = true, underline = true, signs = true })

local root = "/home/gergo/projects/academic-lsp"
local result_file = os.getenv("ACADEMIC_LSP_NVIM_RESULT")
local done = false

local function finish(ok, message)
  if done then return end
  done = true
  local f = assert(io.open(result_file, "w"))
  f:write((ok and "OK" or "FAIL") .. "\n" .. message .. "\n")
  f:close()
  vim.cmd("qa!")
end

vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if client and client.name == "academic-lsp" then
      vim.defer_fn(function()
        local diagnostics = vim.diagnostic.get(0)
        if #diagnostics == 0 then
          finish(false, "academic-lsp attached but no diagnostics were published")
          return
        end
        for _, diagnostic in ipairs(diagnostics) do
          if diagnostic.message:find("LSP", 1, true) then
            finish(true, diagnostic.message)
            return
          end
        end
        finish(false, "diagnostics were published, but none mentioned LSP")
      end, 1200)
    end
  end,
})

vim.api.nvim_create_autocmd("BufReadPost", {
  callback = function()
    vim.lsp.start({
      name = "academic-lsp",
      cmd = { "uv", "run", "academic-lsp" },
      cwd = root,
      root_dir = root,
    })
  end,
})

vim.defer_fn(function()
  finish(false, "timed out waiting for academic-lsp diagnostics")
end, 8000)
LUA

result="$tmpdir/result.txt"
XDG_CONFIG_HOME="$tmpdir/config" \
XDG_DATA_HOME="$tmpdir/data" \
XDG_STATE_HOME="$tmpdir/state" \
XDG_CACHE_HOME="$tmpdir/cache" \
ACADEMIC_LSP_NVIM_RESULT="$result" \
nvim --headless "$tmpdir/test.md"

cat "$result"
