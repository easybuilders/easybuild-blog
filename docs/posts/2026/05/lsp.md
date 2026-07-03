---
authors:
  - micket
date: 2026-05-xx
slug: jobs
hide:
  - navigation
---

# LSP for EasyConfig files

Want to have a LSP that gives you hint when using the incorrect name or version of a dependency? Warning on incorrect filename not matching version and name and toolchain? It already exists!

<!-- more -->

## Demonstration

TODO asciinema

## Getting started with EasyErgo

Me and Yunqi wrote a LSP for easyconfig files that will 
1. Display warnings on incorrect version or name strings for (build)dependencies.
2. Warnings when filename doesn't match
3, Possible some more things in the future

You'll find the repo here: <https://github.com/c3se/easyergo> and it can be installing into any venv of choice using 
```
pip install git+https://github.com/c3se/easyergo.git
```

For example, use `uv` to get an environment quickly:

```
uv venv lspvenv
source lspvenv/bin/activate
uv pip install git+https://github.com/c3se/easyergo.git
```

I prefer to run it as a persisten service (it stays running, and many editor sessions can attach to it):

```
easyergo -p 8000 --persistent
```

EasyErgo uses EB's own mechanisms for finding your robot paths, so you can use the standard easybuild configuration and environment variables to point it to your easyconfigs directories.

Neovim has a buildin LSP client, so just create `.config/nvim/init.lua`:

```lua
vim.api.nvim_create_autocmd({"BufEnter", "BufWinEnter"}, {
  pattern = {"*.eb"},
  callback = function(args)
    client_id = vim.lsp.start({
      name = 'easyergo',
      cmd = vim.lsp.rpc.connect('127.0.0.1', 8000)
  })
  end
})
```

and you are done!

## Syntax highlight

Not part of the LSP, but adding this will also massively improve the editing experience in (neo)vim.

Minimum, you should instruct the editor to treat eb files as python, in your `~/.vimrc` you can specify:

```vimrc
autocmd BufNewFile,BufRead *.eb set syntax=python
```

but you can also customize it with a custom `easybuild` syntax:


```vimrc
autocmd BufNewFile,BufRead *.eb set syntax=easybuild
```

where you create `.vim/syntax/easybuild.vim` which we can extend the basic python syntax with EB specifics:

```vimrc
runtime! syntax/python.vim

" Known keywords
syntax keyword eb_CONSTANT
    \ ARCH
    \ EXTERNAL_MODULE
    \ HOME
    \ OS_NAME
    \ OS_PKG_IBVERBS_DEV
    \ OS_PKG_OPENSSL_BIN
    \ OS_PKG_OPENSSL_DEV
    \ OS_PKG_OPENSSL_LIB
    \ OS_PKG_PAM_DEV
    \ OS_TYPE
    \ OS_VERSION
    \ SHLIB_EXT
    \ SYSTEM
    \ SYS_PYTHON_VERSION
    \ APACHE_SOURCE
    \ BITBUCKET_SOURCE
    \ BITBUCKET_DOWNLOADS
    \ CRAN_SOURCE
    \ FTPGNOME_SOURCE
    \ GITHUB_SOURCE
    \ GITHUB_LOWER_SOURCE
    \ GITHUB_RELEASE
    \ GITHUB_LOWER_RELEASE
    \ GNU_SAVANNAH_SOURCE
    \ GNU_SOURCE
    \ GOOGLECODE_SOURCE
    \ LAUNCHPAD_SOURCE
    \ PYPI_SOURCE
    \ PYPI_LOWER_SOURCE
    \ R_SOURCE
    \ SOURCEFORGE_SOURCE
    \ XORG_DATA_SOURCE
    \ XORG_LIB_SOURCE
    \ XORG_PROTO_SOURCE
    \ XORG_UTIL_SOURCE
    \ XORG_XCB_SOURCE
    \ SOURCE_TAR_GZ
    \ SOURCELOWER_TAR_GZ
    \ SOURCE_TAR_XZ
    \ SOURCELOWER_TAR_XZ
    \ SOURCE_TAR_BZ2
    \ SOURCELOWER_TAR_BZ2
    \ SOURCE_TGZ
    \ SOURCELOWER_TGZ
    \ SOURCE_TXZ
    \ SOURCELOWER_TXZ
    \ SOURCE_TBZ2
    \ SOURCELOWER_TBZ2
    \ SOURCE_TB2
    \ SOURCELOWER_TB2
    \ SOURCE_GTGZ
    \ SOURCELOWER_GTGZ
    \ SOURCE_ZIP
    \ SOURCELOWER_ZIP
    \ SOURCE_TAR
    \ SOURCELOWER_TAR
    \ SOURCE_XZ
    \ SOURCELOWER_XZ
    \ SOURCE_TAR_Z
    \ SOURCELOWER_TAR_Z
    \ SOURCE_WHL
    \ SOURCELOWER_WHL
    \ SOURCE_PY2_WHL
    \ SOURCELOWER_PY2_WHL
    \ SOURCE_PY3_WHL
    \ SOURCELOWER_PY3_WHL
    \ VERSION_TAR_GZ
    \ VERSION_TAR_XZ
    \ VERSION_TAR_BZ2
    \ V_VERSION_TAR_GZ
    \ V_VERSION_TAR_XZ
    \ V_VERSION_TAR_BZ2

highlight link eb_CONSTANT Define

" Only known templates:
syntax match eb_TemplateSequences "%(name\(l\(etter\(lower\)\?\|ower\)\)\?)s" containedin=pythonString contained
syntax match eb_TemplateSequences "%(version\(_m\(ajor_m\)\?inor\|_major\|prefix\|suffix\)\?)s" containedin=pythonString contained
syntax match eb_TemplateSequences "%(\(install\|\(start_\|build\)\)dir)s" containedin=pythonString contained
syntax match eb_TemplateSequences "%(\(\(p\(erl\|y\)\|r\)\(short\|\(maj\)\?\)ver\|cuda\(short\|\(maj\)\?\)ver\|java\(short\|\(maj\)\?\)ver\))s" containedin=pythonString contained
syntax match eb_TemplateSequences "%(cuda_\(c\(\(\(ompute_capabilities\|c_cmake\)\|c_semicolon_sep\)\|c_space_sep\)\|sm_\(comma\|space\)_sep\))s" containedin=pythonString contained
syntax match eb_TemplateSequences "%(\(toolchain_\(version\|name\)\|bitbucket_account\|mpi_cmd_prefix\|github_account\|module_name\|parallel\|sysroot\|arch\))s" containedin=pythonString contained

highlight link eb_TemplateSequences Macro

syntax match eb_TrailingSpace /\s\+$/
highlight link eb_TrailingSpace Error
```

## Running as a system service

I have dedicated VM that my easybuild user runs from. I have the it running by default via an system service. Create `~/.config/systemd/user/easyergo.service`:

```ini
[Unit]
Description=EasryErgo
# ConditionHost=*-buildhost  # limit in case of HOME is on shared filesystem

[Service]
ExecStart=bash -l -c "source lspvenv/bin/activate; easyergo -p 8000 --persistent"
Restart=always

[Install]
WantedBy=default.target
```

and enable+run it with:

```bash
systemctl --user enable --now easyergo.service
```


If you also enable lingering for the user, systemd service would auto restart if the host it rebooted, and service stays running if yo log out:

```
sudo loginctl enable-linger $USER
```


## Limitations

A few things complicates perfect analysis as the LSP has to

1. run very fast so one can't read the content of all easyconfigs in the robot paths
2. run when the file is malformed python (as you are actively writing it)
3. Easyconfig file names are not unique since `name` and `version` may both contain dashes and letters and numbers it.

In particular, this makes it very difficult to handle templates. The LSP won't be able to figure out what this string is

```python3
dependencies = [
    ('CUDA', '12.9.0', '', SYSTEM),
    ('PyTorch', '2.3.4', '-CUDA-%(cudaver)s')  # The LSP will struggle with this
]
```

is thus might produce **false errors** or might mess some errors.

## Future development

I might look into a few possible improvements, such as

1. Attempt to resolve common templates for common things like CUDA, Java
2. Autocomplete (instead dof just giving warnings)
3. Deprecation warnings on old variable names
4. Watch for files in robot paths and reload automatically
5. 
