---
authors:
  - thyre
date: 2025-08-21
slug: flexiblas
hide:
  - navigation
---

# A short overview of FlexiBLAS and its flexibility

FlexiBLAS is one of the core components of each modern EasyBuild toolchain.
In this blog post, we'll explore how one can use FlexiBLAS to choose the underlying BLAS library, and what impacts on performance one may expect.

<!-- more -->

## History

When it comes to numerical algorithms, the BLAS libraries are one of the most central ones.
Many other libraries and tools build on top of it, for example LAPACK or MAGMA and Python libraries like NumPy and SciPy.
BLAS has a reference implementation, often called [Reference BLAS](https://www.netlib.org/blas/).
This implementation however is very inefficient, and shouldn't be used for any production code.

There exist many implementations of BLAS, provided by open-source libraries like [OpenBLAS](https://github.com/OpenMathLib/OpenBLAS) or [BLIS](https://github.com/flame/blis), and vendored libraries like [AOCL-BLAS](https://www.amd.com/de/developer/aocl/dense.html), [Intel oneMKL](https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html) and [NVIDIA NVPL](https://developer.nvidia.com/nvpl).
All implement the same general BLAS library, but with their own optimizations for architectures on top, having each their strengths and weaknesses.
Libraries would therefore need to support all of them, combined with their separate library names, flags and so on.
This is cumbersome to do, and forces users into specific libraries.

[FlexiBLAS](https://www.mpi-magdeburg.mpg.de/projects/flexiblas) is a wrapper library that enables the exchange of the BLAS (Basic Linear Algebra System) and LAPACK (Linear Algebra PACKage) implementation used in an executable without recompiling or re-linking it.
Implementations can be chosen via config files, or even at runtime by the user.
This significantly increases flexibility by the user.

EasyBuild has adopted FlexiBLAS for its `gfbf` and `foss` toolchains since `2021a` (May'21), available since EasyBuild v4.4.0.
Back then, default backends only included OpenBLAS and BLIS.
Since then, FlexiBLAS was continously expanded.
`2022a` (EasyBuild v4.5.5) added support for Intel MKL as a backend.
More recently, `2025a` added support for AOCL-BLAS on x86-64 (EasyBuild v5.1.0).
`2025b` will expand this with support for NVPL on aarch64 systems in EasyBuild v5.1.2.

What does this mean for me as a user of these modules?

## Building your application with FlexiBLAS

**TODO**

## Choosing your FlexiBLAS backend

When building from an EasyConfig provided in the EasyBuild repositories, FlexiBLAS will choose OpenBLAS as the default backend. This default can be overwritten with the `flexiblas_default` EasyBlock parameter.

Once installed, available backends can be checked with `flexiblas print`:
```console
$ flexiblas print
[...]
System-wide from config directory ([...]/FlexiBLAS/3.4.5-GCC-14.3.0/etc/flexiblasrc.d/)
 NETLIB
   library = libflexiblas_netlib.so
   comment =
 AOCL_MT
   library = libflexiblas_aocl_mt.so
   comment =
 [...]
 OPENBLAS
   library = libflexiblas_openblas.so
   comment =
[...]
```

The same command also shows the default BLAS library:

```console
$ flexiblas print | grep -A+4 "Default BLAS"
Default BLAS:
    System:       OPENBLAS
    User:         (none)
    Host:         (none)
    Active Default: OPENBLAS (System)
```

This default library can be easily overridden by the user in two ways:

### Default configuration via config file

FlexiBLAS checks a set of files at start-up:

- `${EBROOTFLEXIBLAS}/etc/flexiblasrc`
- `${EBROOTFLEXIBLAS}/etc/flexiblasrc.d/*.conf`
- `${HOME}/.flexiblasrc`
- `${HOME}/.flexiblasrc.$(hostname)`
- `${FLEXIBLAS_CONFIG}`

In these config files, one can specify default runtime options for FlexiBLAS, including the default library.
Setting this in one of the files for example:

```
default = NETLIB
```

causes FlexiBLAS to use the NETLIB reference implementation to be used by default.

```console
$ flexiblas print | grep -A+4 "Default BLAS"
Default BLAS:
    System:       OPENBLAS
    User:         NETLIB
    Host:         (none)
    Active Default: NETLIB (User)
```

This default can also be set directly on the command-line via `flexiblas default`, and removed with the same command without arguments.

```console
$ flexiblas default AOCL_MT
Setting user default BLAS to AOCL_MT.
$ flexiblas default
Removing user default BLAS setting.
```

### Default configuration at runtime

At runtime, users can set the environment variable `FLEXIBLAS` to a known BLAS backend.
This will select the backend instead of any System / User / Host configuration.
This can be checked with `FLEXIBLAS_VERBOSE=1`

### A full example



## Benchmarking FlexiBLAS backends

As mentioned, different BLAS libraries exist, with their benefits and drawbacks. A library might be especially optimized for certain architectures, or might not perfectly support a recently released architecture yet.
While blindly using a BLAS library works just fine, one might leave a lot of performance on the table.

Let's look at how this could be profiled.

### SciPy & NumPy benchmarks

SciPy and NumPy provide a benchmark suite based on [airspeed velocity (asv)](https://github.com/airspeed-velocity/asv).
This is a benchmarking tool, allowing to do continous benchmarking of Python packages over their lifetime to identify performance regressions and determine the commit which introduced them.

Both NumPy and SciPy include these benchmarks in the `benchmark` subdirectory of their GitHub repository, including lots of benchmarks using BLAS routines.
With slight changes to their config file `asv.conf.json`, we can run these benchmarks ourselves to test different BLAS libraries.

### A look at benchmark results

For this blog post, we'll take a look at three different systems:

- AMD Ryzen AI 7 350 (Zen 5), 8 cores / 16 threads, Fedora 42
- AMD Ryzen 7800X3D (Zen 4), 8 cores / 16 threads, Arch Linux
- NVIDIA GH200 (Neoverse V2), 72 cores / 72 threads, RHEL 9

We are using the `2025b` toolchain, which provide all the required modules for the benchmarks.
All modules to reproduce these measurements can be installed with:

```console
$ eb --robot asv-0.6.4-GCCcore-14.3.0.eb SciPy-bundle-2025.07-gfbf-2025b.eb
$ # If on x86-64 platform
$ eb imkl-2025.2.0.eb --accept-eula-for=Intel-oneAPI
```

To run the benchmarks, we'll modify `asv.conf.json` like this (here for NumPy):
```diff
diff --git a/benchmarks/asv.conf.json b/benchmarks/asv.conf.json
index 7c7542b1ec..3d9b94a26f 100644
--- a/benchmarks/asv.conf.json
+++ b/benchmarks/asv.conf.json
@@ -46,9 +46,9 @@
     // list indicates to just test against the default (latest)
     // version.
     "matrix": {
-        "Cython": [],
-        "build": [],
-        "packaging": []
+        "env": {
+            "FLEXIBLAS": ["NETLIB", "AOCL_MT", "IMKL", "BLIS", "OPENBLAS"],
+        },
     },

     // The directory (relative to the current directory) that benchmarks are
```

Once that is done, we can run the NumPy benchmarks like this:

```console
$ export BLIS_NUM_THREADS=<your-cpu-thread-count>
$ asv run --python=same -b "bench_linalg" --set-commit-hash bc5e4f811db9487a9ea1618ffb77a33b3919bb8e
```

and the SciPy benchmarks like this:

```console
$ export BLIS_NUM_THREADS=<your-cpu-thread-count>
$ asv run --python=same -b ".*linalg.*" --set-commit-hash 0cf8e9541b1a2457992bf4ec2c0c669da373e497
```

On the first run, airspeed velocity will ask a few questions about your system.
This information will be displayed later on.
asv will then run all benchmarks for the specified BLAS libraries by setting `FLEXIBLAS=<BLAS-lib>`, taking time measurements for each. They will be stored in separate JSON files, which can then be evaluated further.

Once all benchmarks have finished, you can run the following commands:

```console
$ asv publish
[11.11%] · Loading machine info
[22.22%] · Getting params, commits, tags and branches
[33.33%] · Loading results.....
[44.44%] · Detecting steps.
[55.56%] · Generating graphs
[66.67%] · Generating output for SummaryGrid
[77.78%] · Generating output for SummaryList
[88.89%] · Generating output for Regressions
[100.00%] · Writing index
$ asv preview
· Serving at http://127.0.0.1:8080/
· Press ^C to abort
```

You can then follow the link to explore the results.

**TODO**

## Takeaway

There are many different BLAS implementations. EasyBuilds supports a whole bunch of them in recent toolchains. Depending on your application, it might be worthwhile to explore which backend yields the best performance.

Simply set

```console
export FLEXIBLAS=<your-backend>
```

and you will be able to switch from OpenBLAS to a backend of your choice!
Don't forget to link FlexiBLAS via `-lflexiblas` instead of using a BLAS library directly.
