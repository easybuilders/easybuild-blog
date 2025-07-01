---
authors:
  - boegel
date: 2025-05-27
slug: easybuild-5.1.0
hide:
  - navigation
---

# EasyBuild v5.1.0

EasyBuild v5.1.0 was released on 26 May 2025.

This version includes a couple of changes and enhancements we want to briefly highlight in this blog post.

For a detailed overview of all changes included in EasyBuild v5.1.0, [see the release notes](https://docs.easybuild.io/release-notes/#release_notes_eb510).

<!-- more -->

---


## Build summary

EasyBuild v5.1.0 will print a summary of the installations that were planned for a particular session,
and indicate whether each installation was a *success*, which ones *failed*, and which installations were *skipped*
(for example because a required dependency failed to install).

For example:

```
$ eb matplotlib-3.9.2-gfbf-2024a.eb -r
...
== Build succeeded for 2 out of 4
== Summary:
   * [SUCCESS] Python/3.12.3-GCCcore-13.3.0
   * [SUCCESS] SciPy-bundle/2024.05-gfbf-2024a
   * [FAILED]  libpng/1.6.43-GCCcore-13.3.0
   * [SKIPPED] matplotlib/3.9.2-gfbf-2024a
```

With this summary you can more easily assess the overall result of the EasyBuild session, and quickly focus on the failing installations. 

---

## CUDA sanity check

Starting with EasyBuild v5.1.0, additional checks are being done during the sanity check step
for installations in which CUDA is used as a dependency.

Binaries, libraries, and compiled Python modules are inspected by EasyBuild using the
[`cuobjdump` binary utility](https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html)
that comes with the CUDA SDK, to determine whether they have the expected *device and/or PTX code*.

CUDA device code is a binary file format for executables that can be run on NVIDIA GPUs.

PTX is an intermediate binary format for NVIDIA GPUs, which can be [Just-In-Time (JiT) compiled](https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/#just-in-time-compilation)
to run on a specific NVIDIA GPU.

In short: EasyBuild verifies in the CUDA sanity check to what extent the hardware targets supported by the binaries,
libraries, and compiled Python modules correspond with the CUDA compute capabilities that EasyBuild was configured
to use (see the `cuda-compute-capabilities` configuration setting, and the `cuda_compute_capabilities` easyconfig parameter).

Various related configuration settings are supported since EasyBuild v5.1.0, which all start with `cuda-sanity-check`.
They specify how strict EasyBuild should be when performing the CUDA sanity check:

* Does PTX code *need* to be available? (`cuda-sanity-check-accept-missing-ptx`, disabled by default);
* Is device code for the specified CUDA compute capabilities required, or is equivalent PTX code sufficient?
  (`cuda-sanity-check-accept-ptx-as-devcode`, disabled by default);
* Is device code for additional CUDA compute capabilities allowed? (`cuda-sanity-check-strict`, disabled by default)

For now, EasyBuild will by default only print and/or log warnings when the specified conditions are not met,
unless the `cuda-sanity-check-error-on-failed-checks` configuration setting is enabled.

For installations in which CUDA is used as a (direct) dependency,
the trace output for the sanity check step will include a brief summary like:
```
  >> CUDA sanity check summary report:
  >> Number of CUDA files checked: 7
  >> Number of files missing one or more CUDA Compute Capabilities: 2
  >> (not running with --cuda-sanity-check-error-on-failed-checks, so not considered failures)
  >> Number of files with device code for more CUDA Compute Capabilities than requested: 3
  >> (not running with --cuda-sanity-check-error-on-failed-checks, so not considered failures)
  >> Number of files missing PTX code for the highest configured CUDA Compute Capability: 5
  >> (not running with --cuda-sanity-check-error-on-failed-checks, so not considered failures)
  >> You may consider rerunning with --cuda-sanity-check-accept-ptx-as-devcode to accept suitable PTX code instead of device code.
  >> You may consider running with --cuda-sanity-check-accept-missing-ptx to accept binaries missing PTX code for the highest configured CUDA Compute Capability.
  >> See build log for detailed lists of files not passing the CUDA Sanity Check
```

For in-depth details on this, see the changes that were made in [`easybuild-framework` PR #4692](https://github.com/easybuilders/easybuild-framework/pull/4692/files).

---

## Data installations

EasyBuild v5.1.0 adds support for installing datasets as modules.

Sam Moors (VUB) gave a talk about this idea at EUM'24 (see [slides](https://users.ugent.be/~kehoste/eum24/019_eum24_datasets.pdf) + [recording](https://www.youtube.com/watch?v=13q_aKDDv9k&list=PLhnGtSmEGEQild9FmlP8Qmz9Csc_gOJKF&index=20&pp=gAQBiAQB)).

Datasets get special treatment in terms of where they are installed, and how their "source" files are managed.

For more information, see [https://docs.easybuild.io/datasets](https://docs.easybuild.io/datasets).

---

## Downloading pull request diff via GitHub API

The mechanism for determining the files that were changed in a pull request when `--from-pr` or
`--include-easyblocks-from-pr` is used has been changed in EasyBuild v5.1.0, to use the GitHub API rather than downloading a `*.diff`
file from `https://github.com`.

This was done to mitigate the impact of [changes made by GitHub to impose stricter rate
limits](https://github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/)
for the GitHub web interface, which can quickly lead to an HTTP error when downloading too frequently:
```
HTTP Error 429: Too Many Requests
```

For more details, see [framework issue #4869](https://github.com/easybuilders/easybuild-framework/issues/4869) and [framework PR #4878](https://github.com/easybuilders/easybuild-framework/pull/4878).

---

## Cleaner output for sanity check

The output produced by the sanity check step has been cleaned up in EasyBuild v5.1.0,
by replacing the standard (noisy) trace output for commands executed during the sanity check with a one-line message.

The output for the "import" tests that are run for every extension that is being installed is now a lot cleaner.
It used to be multiple lines with way too much detail for each extension:

```
>> running shell command:
      /software/Python/3.12.3-GCCcore-13.3.0/bin/python -c "import matplotlib"
      [started at: 2025-05-23 09:15:19]
      [working dir: /software/matplotlib/3.9.2-gfbf-2024a]
      [output and state saved to /tmp/eb-sec1umjh/run-shell-cmd-output/python-d3adb33f]
>> command completed: exit 0, ran in < 1s
```

It now is just a single line per extension:

```
>> Extension sanity check command '/software/Python/3.12.3-GCCcore-13.3.0/bin/python -c "import matplotlib"': OK
```

Likewise for the `pip check` command that is run in the sanity check step when Python packages are being installed.
This used to result in output like:
```
== sanity checking...
  >> running shell command:
        python -m pip check
        [started at: 2025-05-23 10:26:11]
        [working dir: /tmp/easybuild/Python/3.13.1/GCCcore-14.2.0]
        [output and state saved to /tmp/eb-d_ec_z2f/run-shell-cmd-output/python-d3adb33f]
  >> command completed: exit 0, ran in < 1s
```

Now, it's a lot shorter:

```
== sanity checking...
  >> Check on requirements for installed Python packages with 'pip check': OK
```

---

## 2025a common toolchains

Easyconfig files for the `2025a` update of the common toolchains `foss` and `intel` are included with EasyBuild v5.1.0.

Note that the `2024b` version of the common toolchains was skipped, mostly due to focusing on releasing EasyBuild
v5.0.0 in the period in which the `2024b` update of the common toolchains was supposed to be defined.

For more details, see the [overview of common toolchains](https://docs.easybuild.io/common-toolchains/#common_toolchains_overview).

---

## Notable bug fixes

Beyond the highlights covered above, there are a couple of small bug fixes included in EasyBuild
v5.1.0:

- The `pip check` command is now executed only *once* in the sanity check for an installation that involves Python packages, which makes sense since this is a global check (not for a specific Python package).
- Earlier versions of EasyBuild included a silly bug that could lead to messages like "`Fetching files: 100% (4/3)`" being shown in
  the download progress bar. This silly problem has been resolved in EasyBuild v5.1.0.
- Since EasyBuild v5.0.0, the path to the `lib` subdirectory of a software installation directory was being added to the `$CMAKE_LIBRARY_PATH` environment variable in environment module files generated
  by EasyBuild, while this was not the intention. This bug has been squashed in EasyBuild v5.1.0.
- The `--ignore-test-failure` EasyBuild configuration setting was partially broken since EasyBuild v5.0.0: errors that
  were raised during the test step were not actually being ignored. This rendered `--ignore-test-failure` useless for
  ignoring a handful of failing tests when installing PyTorch, for example.
  This regression was fixed in EasyBuild v5.1.0.
- Several small issues have been fixed in the custom easyblock for LLVM, which was thoroughly revised in EasyBuild
  v5.0.0.
