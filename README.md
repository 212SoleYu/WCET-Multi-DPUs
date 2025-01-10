# Overview

This scirpt is a single demonstration version our WCET analysis method.

This script could compute the WCET bound  based on our analysis method for single-DPU and multi-DPUs situations.

This script is not limited to the included CNNs types and can be extended by providing the numbers of bus transacations  and the connection ways of DPU ports for any other CNN models.

User only need to modify **TRANSACTION_PARAMETERS** and **ALL_CONNECTION** in WCET.py to customize the DPU configuration.

# Execution Example

## Requirement

Python 3.9.0 and later versions.

## Run

No additional parameters are required for script execution:

```shell
python3 ./WCET.py
```

And the output will include :

1. The current connection ways of DPU ports.
2. The basic WCET bound for a single DPU without any contention.
3. The extra WCET caused by contention between DPUs.
4. The total WCET bound of our analysis method.

An output example:

```shell
Display the current connection:
3 DPU(s) in total

DPU 0:
Model: yolov4
INS port: LPD
Data0 port: HP0
Data1 port: HP1

DPU 1:
Model: yolov4
INS port: LPD
Data0 port: HP2
Data1 port: HP3

DPU 2:
Model: mobilenetv2
INS port: LPD
Data0 port: HPC0
Data1 port: HPC1


Modelname: yolov4
T_R_BASE: 0.092334 s
T_INS_BASE: 0.024485 s
T_W_BASE: 0.039205 s

T_R_EXTRA: 0.088340 s
T_INS_EXTRA: 0.027044 s
T_W_EXTRA: 0.022280 s

yolov4 base time: 0.09233394 s
yolov4 extra time: 0.08834023333333334 s
yolov4 total time: 0.18122417333333332 s

Modelname: yolov4
T_R_BASE: 0.092334 s
T_INS_BASE: 0.024485 s
T_W_BASE: 0.039205 s

T_R_EXTRA: 0.089009 s
T_INS_EXTRA: 0.027044 s
T_W_EXTRA: 0.021594 s

yolov4 base time: 0.09233394 s
yolov4 extra time: 0.08900943333333333 s
yolov4 total time: 0.18189337333333333 s

Modelname: mobilenetv2
T_R_BASE: 0.007527 s
T_INS_BASE: 0.006596 s
T_W_BASE: 0.000929 s

T_R_EXTRA: 0.015413 s
T_INS_EXTRA: 0.009175 s
T_W_EXTRA: 0.001655 s

mobilenetv2 base time: 0.007527036666666666 s
mobilenetv2 extra time: 0.015413066666666666 s
mobilenetv2 total time: 0.023140103333333332 s

```

