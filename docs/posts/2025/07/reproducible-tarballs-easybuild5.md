---
authors:
  - lexming
date: 2025-07-30
slug: reproducible-tarballs-eb5
hide:
  - navigation
---

## The Journey to Reproducible Tarballs of Git sources in EasyBuild 5.0

One of the important milestones reached with EasyBuild 5 is **support for
reproducible tarballs** when sourcing code directly from Git repositories.
While the concept may sound simple, basically _just make the tarball the same
every time_, the path to get there was anything but straightforward.

This post tells the story of how we got reproducible tarballs for sources from
Git repos working reliably in EasyBuild, and why it took more than just
flipping a flag in `tar`.

<!-- more -->

---

### Why tarballs for sources from Git?

EasyBuild supports fetching sources from various origins, and Git repositories
are often used when official source tarballs are unavailable or when working
with development unreleased code. In these cases, EasyBuild will create a
source archive by checking out a specific Git commit or tag and generating a
compressed `.tar` file from it.

The fetch operation from the Git repository is reliable and Git will verify the
integrity of all downloaded files. However, Git cannot guarantee that you are
getting the exact same code base by executing the same clone command in two
different moments in time. For instance, the developers can change the commit
referenced by a _tag_ (which is not so uncommon!). In such a case, cloning the
same tag will lead to a different code base.

EasyBuild avoids this pitfall by fetching the sources from the target Git
repository once, then generate a tarball with its SHA256 checksum. Hence, by
sharing this checksum among the EasyBuild community, we can be sure that every
installation of the target software and version will use the same exact code
base and guarantee it's reproducibility.

But here's the catch: without careful handling, **the resulting tarball isn't
guaranteed to be identical** every time you build it, even if the Git commit
hasn't changed.

---

### The reproducibility problem

The issue stems from how traditional `tar` commands behave. By default, `tar`
includes:

* File metadata (_i.e._ modification timestamps or ownership)
* The order in which files appear in the archive (which may vary)
* Potential system-specific quirks (_e.g._ file permissions or sorting behavior)

This means that building on different systems, or even just building twice on
the same system, can yield **bitwise-different tarballs** despite containing
the same source files with the same contents.

---

### First Steps: Making deterministic tarballs

The work began with [PR#4248](https://github.com/easybuilders/easybuild-framework/pull/4248),
which tackled the core problem: **making the tarballs generated from Git
repositories deterministic**. We followed the recommendations from
[reproducible-builds.org](https://reproducible-builds.org/docs/archives/) and
the [GNU Project](https://www.gnu.org/software/tar/manual/html_node/Reproducibility.html).

We initially switched to using a custom `tar` command that:

* Normalizes file modification times (_i.e._ set all modification times to epoch 0)
* Enforces a fixed file order
* Avoids embedding user or group names (_i.e._ all files owned by UID 0)

Then we had to deal with the compression method. Typically tarballs in
EasyBuild are compressed with GZip and by default, GZip injects the timestamps
in the metadata of the compressed file. So we also added a custom `gzip`
command into the mix:

* Avoid time-dependent metadata in GZip files (_i.e._ `--no-name`)

These small but crucial changes meant that given the same Git commit, you would
now get **the exact same `.tar.gz` file**, regardless of where or when you
built it.

---

### Hidden Challenges Across Systems

However, the devil hides in the details and in this case it was the rich
ecosystem of Unix-like operating systems. Different systems ship with different
versions of `tar` and `gzip`, and not all of them support the flags needed for
reproducible archives. For instance:

* `--sort=name` was not available in older versions of GNU tar
* macOS uses BSD tar by default, which behaves differently
* Some systems used `gzip` versions that ignored key reproducibility flags

As a result, although the solution we implemented in EasyBuild was correct,
**testing across platforms** revealed inconsistencies and broken cases. Those
were effectively unsolvable in EasyBuild as our users in many cases cannot
control what variant of the `tar` command  or other tools are installed in
their host system.

---

### Switching from system tools to Python

Given the aforementioned complexities found in system tools across Unix-like
systems, we decided to not rely any more on the host system and switch to a
solution purely implemented in Python. This code refactoring happened in [PR
#4660](https://github.com/easybuilders/easybuild-framework/pull/4660),
leveraging the [tarfile module in the Standard Python
Library](https://docs.python.org/3/library/tarfile.html) to generate archives
of sources from Git repositories.

The implementation in Python did indeed free us from the variability in the
tooling available on the host system. However, we now faced the variability of
Python versions. EasyBuild 5 supports all versions from Python 3.6 to 3.12.
That's a quite large range of versions **with 7 years of development!** And in
that time frame many things changed.

In Python 3.9, the `tarfile` module changed the way it writes headers in the
tar archive [python/cpython#90021](https://github.com/python/cpython/issues/90021).
Although this change was only announced for tarfiles in `PAX_FORMAT`, our tests
showed that it also applied to the `GNU_FORMAT` used in EasyBuild. This means
that tarfiles generated by EasyBuild cannot be reproduced across all supported
Python versions. Generating the archive in Python 3.6 to 3.8, will result in a
file that is bitwise-different than the archive generated in Python 3.9 to 3.12.
Fortunately, this change happened in a relatively old version of Python, and
since we already plan to drop support for Python versions older than 3.9, it
did make sense to keep the switch to a Python implementation given all the
advantages gained by avoiding system tools.

The final hurdle was the compression method. Python does provide a module in
its Standard Library to compress with GZip, as we were already doing for
archives in EasyBuild. However, at the time of development this `gzip` module
did not support the needed features (_i.e._ `--no-name` option) found in the
`gzip` command to make a reproducible tarball. Therefore, we changed the
compression algorithm for reproducible tarballs to
[LZMA](https://docs.python.org/3/library/lzma.html) in EasyBuild 5, which does
not inject any system-dependent or time-dependent metadata into the compressed
file.

---

### A Small Feature, A Big Step

This development manifests as a simple outcome for users: when you use the
`git_config` parameter in an easyconfig and build on multiple machines, **you
get the same source tarball (almost) every time**. The only caveats being that:

1. the format of the archive is set to `.tar.xz`, which is already the default
   in all easyconfig files published in our public repository
2. at least Python 3.9 is used, which is already found in all current versions of
   the major Linux distributions

The benefits for users of EasyBuild 5 are:

* **Verifiable provenance**: You can compare tarballs and confirm they're identical
* **Build consistency**: Downstream builds behave identically
* **Audit readiness**: You can reproduce the build environment for scientific or security reviews

### In Closing

Reproducibility is a foundational principle in scientific computing, and
EasyBuild 5.0 makes a meaningful contribution by ensuring that even Git-based
sources can be fetched and packaged deterministically. It was a small battle,
fought line by line across platforms and tar options, but one that brings us
closer to truly reproducible software stacks.

