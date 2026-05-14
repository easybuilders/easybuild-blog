---
authors:
  - micket
date: 2026-04-26
slug: jobs
hide:
  - navigation
---

# Building software with slurm jobs using EasyBuild

This blogpost serves as inspiration and get you started running jobs based on some of the stuff I run on my clusters.

Do you want to conveniently build modules in a hurry? Then you will love `--job`  combined with `-r`.

<!-- more -->

## What is does

By specifying `eb -r --job Foobar-1.2.3-foss-2025b.eb` easybuild will
1. Resolves all dependencies
2. Pre-fetch all the sources
3. Submit jobs for each easyconfig that needs to be built
   - Jobs have dependency tracking based on their dependencies

And then you'll see
```
$ squeue --me

             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           9015294      vera Foobar-1      you PD       0:00      1 (Dependency)
           9015292      vera Stuff-1.      you  R       0:06      1 node-01
           9015293      vera Thing-2.      you  R       0:06      1 node-02
```

You can specify `--job-cores=X` to pick the size of your job.

## Passing SLURM flags

What if your job needs a GPU partition, or specify a TRES?
Set them via environment variables:



```bash
SBATCH_GPUS_PER_NODE=H100:1 eb -r --job-cores=8 Foobar-1.2.3-foss-2025b-CUDA-12.8.0.eb
```

In fact, why not make an alias for it?

```bash
alias buildH100='SBATCH_GPUS_PER_NODE=H100:1 eb -r --job'
```

Depending on your cluster, you may find the following environment variables useful:

```bash
SBATCH_GPUS_PER_NODE
SBATCH_CONSTRAINT
SBATCH_PARTITION
SBATCH_ACCOUNT
```

but of course, many more exist.

## Collect build logs

If you don't want job logs in your current working directory when you submit, collect them to one place using `--job-output=/path/to/logs` .
If you have multiple cluster or architectures, you may wish to place them in specific locations.

Remember that you can set this via environment variables as well, e.g:


Remember that you can set this via environment variables as well, e.g:

```bash
export EASYBUILD_JOB_OUTPUT_DIR=$HOME/log_${CLUSTER_NAME}_${ARCH}/
```


## Debug failed builds

If you have a problem build and the job logs isn't that useful, you can redirect tmpdir to persistent storage:
```bash
--tmpdir=/your/centrestorage/path/eb-tmp
```


A handy alias to nicely keep track of your job queue can be made:


### Simple
A handy alias to nicely keep track of your job queue can be made:


```bash
alias q='squeue --me -O jobid:10,tres-per-node:18,name:60,TimeUsed:10,reasonlist'
alias wq='watch -c \"squeue --me -O jobid:10,tres-per-node:18,name:60,TimeUsed:10,reasonlist\"'
Using `bat`, we can even color the output nicely:


### Colorful

Using `bat`, we can even color the output nicely:


```bash
alias wq="watch -c \"squeue -u c3-builder -O jobid:10,tres-per-node:18,name:60,TimeUsed:10,reasonlist | sed 's/^ *//g' | sed 's/ \+/,/g' | bat -f -l csv --style plain --theme=ansi | column -s, -t | bat --style grid\""
```

### Advanced

Why not look at sacct as well? And color based on state?

```python linenums="1"
#!/usr/bin/env python3

import subprocess
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

SACCT_LIMIT=timedelta(hours=12)

def run(cmd):
    return subprocess.check_output(cmd, text=True).strip().splitlines()


def parse_table(lines):
    header = lines[0].split("|")
    rows = []
    for line in lines[1:]:
        cols = line.split("|")
        rows.append(dict(zip(header, cols)))
    return rows


def parse_gpu(tres_str):
    tres = [x.split('=')[0] for x in tres_str.split(',')]
    for t in tres:
        if 'gpu' in t:
            return t.split(':')[1]
    return ''


def dhms_to_hms(dhms: str) -> str:
    """
    Convert Slurm elapsed time D-HH:MM:SS or HH:MM:SS into HHH:MM:SS
    """
    if '-' in dhms:
        days, hms = dhms.split('-', 1)
        hours, minutes, seconds = map(int, hms.split(':'))
        total_hours = int(days) * 24 + hours
        return f"{total_hours:3}:{minutes:02}:{seconds:02}"
    else:
        return dhms
        hours, minutes, seconds = map(int, dhms.split(':'))
        total_hours = hours
    return f"{total_hours:3}:{minutes:02}:{seconds:02}"


def fix_path(path, jobid) -> str:
    path = path.replace('/cephyr/users/c3-builder/Vera', '~')
    path = path.replace('/cephyr/users/c3-builder/Alvis', '~')
    return path.replace('%j', jobid)


def get_squeue():
    cmd = [
        "squeue",
        "--me",
        "-o", "%i|%j|%T|%M|%R|%f|%b"
    ]
    lines = run(cmd)
    return parse_table(lines)


def get_sacct():
    start = (datetime.now() - SACCT_LIMIT).strftime("%Y-%m-%dT%H:%M:%S")
    cmd = [
        "sacct",
        "-X",
        "-S", start,
        "--parsable2",
        "-o", "jobid,jobname,state,elapsed,nodelist,reason,constraints,reqtres,stdout"
    ]
    lines = run(cmd)
    return parse_table(lines)


def classify_arch(job):
    c = job.get("constraints", "").lower()
    tres = job.get("tres", "").lower()
    nodes = job.get("node", "").lower()

    cpu_model = 'UNK'
    # explicit constraint wins
    if "zen4" in c:
        cpu_model = "ZEN"
    if "icelake" in c:
        cpu_model = "ICE"
    if "skylake" in c:
        cpu_model = "SKY"

    gpu = parse_gpu(tres)

    # heuristic: GPUs are on specific CPU models in my cluster
    lookup = {'h100': 'ZEN', 't4': 'SKY', 'v100': 'SKY', 'a40': 'ICE', 'a100': 'ICE'}
    return lookup.get(gpu, cpu_model), gpu.upper()


def normalize_squeue(jobs):
    out = []
    for j in jobs:
        entry = {
            "source": "squeue",
            "jobid": j["JOBID"],
            "name": j["NAME"],
            "state": j["STATE"].split()[0],
            "time": dhms_to_hms(j["TIME"]),
            "node": j["NODELIST(REASON)"],
            "tres": j["TRES_PER_NODE"],
            "constraints": j["FEATURES"],
            "stdout": "",
        }
        entry["arch"], entry["gpu"] = classify_arch(entry)
        out.append(entry)
    return out


def normalize_sacct(jobs):
    out = []
    for j in jobs:
        entry = {
            "source": "sacct",
            "jobid": j["JobID"],
            "name": j["JobName"],
            "state": j["State"].split()[0],
            "time": dhms_to_hms(j["Elapsed"]),
            "node": j["NodeList"],
            "tres": j["ReqTRES"],
            "constraints": j["Constraints"],
            "stdout": j["StdOut"],
        }
        entry["arch"], entry["gpu"] = classify_arch(entry)
        out.append(entry)
    return out


def main():
    jobs = normalize_squeue(get_squeue())
    sa = normalize_sacct(get_sacct())
    active_jobids = [j['jobid'] for j in jobs]  # dont double up on active jobs
    jobs += [s for s in sa if s['jobid'] not in active_jobids]

    console = Console(force_terminal=True)
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("JOBID", justify="right")
    table.add_column("STATE")
    table.add_column("ARCH")
    table.add_column("GPU")
    table.add_column("TIME", justify="right")
    table.add_column("NODE")
    table.add_column("NAME")
    table.add_column("OUT")

    for j in jobs:
        state = j['state']
        stdout = ''
        if state.upper() in ("FAILED", "TIMEOUT"):
            state = f"[red]{state}[/red]"
            stdout = fix_path(j['stdout'], j['jobid'])
        elif state.upper() == "COMPLETED":
            state = f"[green]{state}[/green]"
        elif state.upper() == "CANCELLED":
            state = f"[yellow]{state}[/yellow]"
        elif state.upper() == "PENDING":
            state = f"[#888888]{state}[/#888888]"

        arch = j['arch']
        if arch == 'ZEN':
            arch = f"[red]{arch}[/red]"
        else:
            arch = f"[blue]{arch}[/blue]"

        table.add_row(j['jobid'], state, arch, j['gpu'], j['time'], j['node'], j['name'], stdout)
    console.print(table)


if __name__ == "__main__":
    main()
```

example running with `watch --color q_advanced`:

{{
asciinema(
  '../../jobs.cast',
  cols=108,
  rows=25,
  markers=[
    [0, "Start"],
    [1, "Some jobs completing"],
  ],
)
}}

