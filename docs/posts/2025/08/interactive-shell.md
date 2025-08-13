---
authors:
  - branfosj
date: 2025-08-13
slug: interactive-shell
hide:
  - navigation
---

# Interactive Shell to Debug Failed Builds

One of the big enhancements in EasyBuild v5 is the support for starting an [interactive shell to debug failed builds](https://docs.easybuild.io/interactive-debugging-failing-shell-commands/)
by simply running the auto-generated `cmd.sh` script.

We would all prefer that no installation ever fails, but there will be times when they do.

The new interactive shell feature provides a way to explore the build environment and debug the failure.

<!-- more -->

---

## Demo

In the following demo, `bzip2-1.0.8.eb` is being built on an Ubuntu 25.04 (Plucky Puffin) system.
This build uses the `SYSTEM` toolchain, which means that the default system compiler provided by the OS is used - in this case GCC v13.3.0 (`gcc` command).

{{
asciinema(
  '../../interactive-shell-demo-bzip.cast',
  cols=108,
  rows=25,
  markers=[
    [0, "View EasyBuild version"],
    [11, "Start installation"],
    [22, "Build failure"],
    [35, "Enter interactive debug environment"],
    [40, "Repeat failed command"],
    [48, "Explore environment"],
    [57, "Exit environment"]
  ],
)
}}

The compilation failure is because of an incompatibility between the older `binutils` (v2.37, defined as build dependency in the easyconfig file) and the newer GCC.

### The 7 stages of the demo

1. *[00:00]* View EasyBuild version
1. *[00:11]* Installing `bzip2` with EasyBuild: `eb bzip2-1.0.8.eb` (all dependencies have been pre-installed);
1. *[00:22]* Installation fails in `build` step;
1. *[00:35]* Enter interactive debug environment by running the `cmd.sh` script;
1. *[00:40]* Repeat the failed command from shell history (arrow up), see why the build failed;
1. *[00:48]* Explore the environment:
    - Print the working directory (`pwd`)
    - List the loaded modules (`module list`);
    - Check the value of the environment variable `CC` (`echo $CC`);
1. *[00:57]* Exiting the interactive debug environment by running `exit`;

### Avoiding this problem

If you experience this failure then you should be able to build `bzip2-1.0.8.eb` using both the OS `gcc` and `binutils`.
You can instruct EasyBuild to do this using [`--filter-deps=binutils`](https://docs.easybuild.io/manipulating-dependencies/#filter_deps).

