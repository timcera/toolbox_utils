## v5.2.0 (2025-05-10)

### Feat

- added pandas_offset_by_version function

## v5.1.4 (2024-06-24)

### Fix

- finally a version of re.split that does what I want
- remove debugging print function call
- only use re.split on strings
- fix issues from removing tssplit
- fix representation of dataframes as input_ts
- fix of parsing list in strings

## v5.1.3 (2024-06-08)

### Fix

- finished removal of tssplit

## v5.1.2 (2024-06-04)

## v5.1.1 (2024-06-01)

## v5.1.0 (2024-05-27)

### Feat

- change about to return ordereddict

## v5.0.9 (2024-03-31)

## v5.0.8 (2023-12-17)

### Fix

- another go at localizing TimeStamp whether naive of set time zone

## v5.0.7 (2023-12-16)

### Fix

- ambiguous="infer" is no longer available working with a TimeStamp

## v5.0.6 (2023-12-16)

### Refactor

- refactors
- sourcery refactor
- refactor with sourcery

## v5.0.5 (2023-10-13)

## v5.0.4 (2023-08-20)

### Fix

- fix in _normalize_units to be more robust

## v5.0.3 (2023-07-31)

## v5.0.2 (2023-07-30)

## v5.0.1 (2023-07-17)

### Fix

- fix to not use broken versions of pint

## v5.0.0 (2023-07-17)

## v4.0.0 (2023-07-16)

### Fix

- **range_to_numlist**: fixed argument validation of range_to_numlist function that is triggered in wdmtoolbox tests

### BREAKING CHANGE

- a breaking change to make sure wdmtoolbox brings in the correct version

## v3.0.7 (2023-06-02)

### Refactor

- addressed pandas FutureWarning about infer_datetime_format in read_csv

## v3.0.6 (2023-05-29)

### Fix

- still didn't get the versions right
- need the correct version of pint for python 3.8

### Refactor

- now expose range_to_numlist for other toolboxes to use

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
