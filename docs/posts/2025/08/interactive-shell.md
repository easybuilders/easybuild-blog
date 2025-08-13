---
authors:
  - branfosj
date: 2025-08-09
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
  idleTimeLimit=3,
  cols=108,
  rows=25,
  markers=[
    [0, "Start installation"],
    [11, "Build failure"],
    [15, "Enter interactive debug environment"],
    [18, "Repeat failed command"],
    [23, "Explore environment"],
    [32, "Exit environment"]
  ],
)
}}

The failure is because of an incompatibility between the older `binutils` (v2.37, defined as build dependency in the easyconfig file) and the newer GCC.

### The 6 stages of the demo

1. *[00:00]* Installing `bzip2` with EasyBuild: `eb bzip2-1.0.8.eb` (all dependencies have been pre-installed);
2. *[00:11]* Installation fails in `build` step;
3. *[00:15]* Enter interactive debug environment by running the `cmd.sh` script;
1. *[00:18]* Repeat the failed command from shell history (arrow up), see why the build failed;
1. *[00:23]* Explore the environment:
    - List the loaded modules (`module list`);
    - Check the value of the environment variable `CC` (`echo $CC`);
1. *[00:32]* Exiting the interactive debug environment by running `exit`;

### Avoiding this problem

If you experience this failure then you should be able to build `bzip2-1.0.8.eb` using both the OS `gcc` and `binutils`.
You can instruct EasyBuild to do this using [`--filter-deps=binutils`](https://docs.easybuild.io/manipulating-dependencies/#filter_deps).

