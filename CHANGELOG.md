## v3.0.5 (2023-05-07)

## v3.0.4 (2023-03-01)

### Fix

- commit change in submodule
- added tssplit submodule but now pointing at my fork so I can make a small change to work with toolbox_utils
- removed tssplit git submodule

### Refactor

- **tssplit**: explicitly including tssplit as a git submodule

## v3.0.3 (2023-02-24)

### Refactor

- small security refactor in setup.py

## v3.0.2 (2023-02-20)

## v3.0.1 (2023-02-12)

### Fix

- shouldn't use shell

## v3.0.0 (2023-02-04)

## v2.0.0 (2023-01-22)

### BREAKING CHANGE

- removing function used in several toolboxes which requires breaking change

### Refactor

- **merge_dicts**: removed tsutils.merge_dicts and replaced with {**x, **y} in all toolboxes

## v1.0.4 (2023-01-16)

### Fix

- fixed force_freq which was working and then NAs were dropped reversing what force_freq did

### Refactor

- refactor using refurb and pylint

## v1.0.3 (2023-01-08)

## v1.0.2 (2022-12-29)

### Refactor

- evaluating new formatting style with blank lines separating code blocks

## v1.0.1 (2022-10-29)

### Fix

- limit the pint version to work on python 3.8, 3.9, 3.10

## v1.0.0 (2022-10-12)

### BREAKING CHANGE

- breaking change because all toolboxes that used typic now need to change to pydantic

### Feat

- removed all typic and replaced with pydantic

### Fix

- removed hspf_reader as dependency and added needed code to toolbox_utils to support hspf_reader functions

## v0.1.2 (2022-09-27)

## v0.1.1 (2022-09-26)

### Fix

- fixed header=0 for pd.read_excel instead of header="infer" which was failing 3.8+ and added tests
