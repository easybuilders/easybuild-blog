---
authors:
  - branfosj
date: 2025-08-09
slug: interactive-shell
hide:
  - navigation
---

# Interactive Shell to Debug Failed Builds

One of the big enhancements in EasyBuild v5 is the addition of an [interactive shell to debug failed builds](https://docs.easybuild.io/interactive-debugging-failing-shell-commands/).

We would all prefer that no build fails, but there will be times when they do.
The new interactive shell feature provides a way to explore the build environment and debug the failure.

<!-- more -->

---

## Demo

In the following demo, `bzip2-1.0.8.eb` is being built on an Ubuntu 25.04 (Plucky Puffin) system.
This build uses the `SYSTEM` toolchain, which means that the OS default compiler is used - in this case `gcc` v13.3.0.
The failure is because of an incompatibility between the older `binutils` (v2.37, as defined in the easyconfig) and the newer `gcc`.

{{
asciinema(
  '/asciinema/bzip-failure.cast',
  idleTimeLimit=3,
  cols=108,
  rows=25,
  markers=[
    [0, "Start build"],
    [11, "Build failure"],
    [15, "Enter debug environment"],
    [18, "Repeat failed command"],
    [23, "Explore environment"],
    [32, "Exit environment"]
  ]
)
}}

### The six stage of the demo

1. EasyBuild of `bzip2`: `eb bzip2-1.0.8.eb` (all dependencies have been prebuilt)
1. Build fails
1. Enter debug environment, sourcing the _interactive shell script_
1. Repeat the failed command, to see the reason for the failure
1. Explore the environment:
    1. list the loaded modules
    1. check the defined value of the environment variable `CC`
1. Exiting the debug environment

### Avoiding this problem

If you experience this failure then you should be able to build `bzip2-1.0.8.eb` using both the OS `gcc` and `binutils`.
You can instruct EasyBuild to do this using [`--filter-deps`](https://docs.easybuild.io/manipulating-dependencies/#filter_deps).

