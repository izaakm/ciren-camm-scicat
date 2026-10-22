---
title: CLI Reference
layout: default
nav_order: 4
has_children: true
---

# CLI Command Reference

`cammcat` is organized as a single entry point with subcommands:

```bash
cammcat [global options] <command> [command options]
```

Run `cammcat <command> --help` at any time to see the full, authoritative
list of options for that command.

## Commands

| Command                                | Purpose 
| ---                                    | ---
| [`cammcat add`](add.md)                | Copy a dataset (file or folder) into the CAMM data repository, optionally computing/verifying checksums. 
| [`cammcat create`](create.md)          | Build dataset metadata and register a new dataset (and its data block) in SciCat. 
| [`cammcat list`](list.md)              | List datasets already registered in SciCat. 
| [`cammcat list-files`](list-files.md)  | List the files attached to one or more datasets. 
| [`cammcat show`](show.md)              | Print the full metadata record for one or more datasets. 
| [`cammcat login`](login.md)            | Authenticate against SciCat and verify credentials work. 
| [`cammcat model`](model.md)            | Inspect the dataset's underlying data model (e.g. dump its JSON schema). 
| [`cammcat config`](config.md)          | Inspect configuration loaded from a config file. 
| [`cammcat help`](help.md)              | Show available settings and their current resolved values. 
| `cammcat attach`                       | (**Not Implemented**) Attach data files to an existing dataset.
| `cammcat update`                       | (**Not Implemented**) Update an existing dataset's metadata.


<!-- END -->
