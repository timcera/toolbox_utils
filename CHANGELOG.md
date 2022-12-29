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
