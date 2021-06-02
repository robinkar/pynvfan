import time

import clr
from System import Int32

clr.AddReference("NvAPIWrapper")
import NvAPIWrapper.Native
from NvAPIWrapper.Native.GPU import CoolerPolicy


def getGPU():
    return NvAPIWrapper.GPU.PhysicalGPU.GetPhysicalGPUs()[0]

def getSensor(gpu):
    for s in gpu.ThermalInformation.ThermalSensors:
        return s

def getCooler(gpu):
    for c in gpu.CoolerInformation.Coolers:
        return c

def calc_speed(speeds, t):
    # Less than min temp
    if t <= speeds[0][0]:
        return 0
    # Higher than max temp
    if t >= speeds[-1][0]:
        return speeds

    higher = list(filter(lambda s: t > s[0], speeds))

    base = higher[-1]
    next_ = speeds[speeds.index(base)+1]
    (t1, f1) = base
    (t2, f2) = next_

    # Linear scaling between the points
    k = (f2-f1)/(t2-t1)
    return int(f1+(t-t1)*k)

def main():
    NvAPIWrapper.NVIDIA.Initialize()
    gpu = getGPU()
    if gpu == None:
        print("No GPU found")
        NvAPIWrapper.NVIDIA.Unload()
        return
    print("Found GPU: {}".format(gpu))

    cooler = getCooler(gpu)
    ci = gpu.CoolerInformation

    speeds = [(50, 27), (60, 27), (70, 31), (80, 45), (90, 100)]

    to_print = ""
    while True:
        try:
            speed = calc_speed(speeds, getSensor(gpu).CurrentTemperature)
            # Let GPU reach the second temp point before cooling down to first temp point
            if speed == speeds[0][1] and not ci.CurrentFanSpeedInRPM:
                speed = 0
            ci.SetCoolerSettings.Overloads[Int32, CoolerPolicy, Int32](cooler.CoolerId, CoolerPolicy.Manual, speed)
            # Overwrite the last line when printing
            last = len(to_print)
            to_print = "{}°C RPM: {}, T: {}".format(getSensor(gpu).CurrentTemperature, ci.CurrentFanSpeedInRPM, speed)
            print("\r{}\r{}".format(" "*last, to_print), end="", flush=True)
            time.sleep(1)
        except:
            break

    ci.RestoreCoolerSettingsToDefault()
    NvAPIWrapper.NVIDIA.Unload()

if __name__ == "__main__":
    main()