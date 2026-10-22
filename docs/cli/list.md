---
title: cammcat list
parent: CLI Reference
layout: default
---

```
$ cammcat list
```

List datasets currently registered in SciCat.


## Usage

```bash
cammcat list [options]
```


## Options

|  Option                         |  Description 
| ---                             | ---
|  `--fields`, `--format`, `-f`   |  Comma-separated list of dataset fields to print (not case-sensitive). Default: `pid,datasetName`. 
|  `--sep SEP`                    |  Column separator (default: a tab character). 
|  `--parsable`, `-p`             |  Shortcut for `--sep "|"`.


## Output

The first line printed is the header row (the field names), followed by
one line per dataset.


## Examples

Default listing:

```bash
cammcat list
```

Choose fields and a pipe-delimited, script-friendly format:

```bash
cammcat list --fields pid,datasetName,owner,creationTime --parsable | column -t -s "|"
```

<!-- END -->
