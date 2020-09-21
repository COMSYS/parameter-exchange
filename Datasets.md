# Datasets

## Overview

This repository contains two real-world datasets that can be used for the evaluation of our implementation:
1. A dataset containing injection molding data for the production of toy bricks.
2. A dataset composed of machine tool parameters.

In the directory `src/tools`, we provide scripts that translate the original datasets into the format required by our implementation.

## Injection Molding

*This dataset was provided by the [institute for plastics processing (IKV)](https://www.ikv-aachen.de/) at [RWTH Aachen](https://www.rwth-aachen.de/)*

**Files:**

- Original Dataset: `data/ikv_data_unconverted.json`
- Converted Dataset: `data/ikv_data.txt`
- Parser/Converter: `tools/ikv_parser.py`

**Description:**

The data records describe the production of toy bricks with an injection molding machine.
The first 21 values in the converted dataset equal the geometry parameter in the original dataset.
These geometry parameters act as input parameters.
The remaining values consist of six machine parameters (X in the original dataset) and one quality indicator describing the resulting part weight (Y in the original dataset).
The machine parameters are (in the same order):

- injection volume flow
- melt temperature
- mold temperature
- packing pressure
- packing pressure time
- cooling time

In total, each record consists of 28 parameters.
For each geometry representing one type of brick, the dataset contains 77 combinations of machine and quality parameters.
As the input parameters are equal, these 77 records have the same identifier for our design.
Moreover, there are records for 60 different toy bricks.
This yields 4620 records in total.


## Machine Tools

*This dataset was provided by the Laboratory for [Machine Tools and Production Engineering (WZL)](https://www.wzl.rwth-aachen.de/) of [RWTH Aachen](https://www.rwth-aachen.de/)*

**Files:**

- Original Dataset: `data/wzl_data_unconverted.json`
- Converted Dataset: `data/wzl_data.txt`
- Parser/Converter: `tools/wzl_parser.py`

**Description:**
The dataset consists of 600 records, each being composed of 17 input and 2 output parameters.
The input parameters define machine configuration values, while the output parameters define the cutting conditions of the milling cutter (Cutting speed (vc) and feed per tooth (fz)).
Some input parameters represent doubles, while others represent textual parameters such as machine types.
These are mapped to integers, as our system can only handle numbers.
Therefore, each converted records only consists of numbers.
The same textual value is mapped to the same integer.
As each record of this dataset has unique input parameters, the set yields 600 unique identifiers.


