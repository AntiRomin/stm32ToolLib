# I2C peripheral input clock
pclkFreq = 48000000
# I2C output clock
i2cFreq = 200000
# Coefficient of Digital Filter
dfcoeff = 2
# If use Analog filter
isUseAF = False

scldel = 0
sdadel = 0
sclh = 0
scll = 0

def i2cClockComputeRaw(pclkFreq, i2cFreq, presc, dfcoeff):
    # Values from I2C-SMBus specification
    # Rise time (max)
    trmax = 0
    # Fall time (max)
    tfmax = 0
    # SDA setup time (min)
    tsuDATmin = 0
    # SDA hold time (min)
    thdDATmin = 0
    # High period of SCL clock (min)
    tHIGHmin = 0
    # Low period of SCL clock (min)
    tLOWmin = 0

    # Silicon specific values, from datasheet
    if isUseAF:
        tAFmin = 50
    else:
        tAFmin = 0

    # Actual (estimated) values
    # Rise time
    tr = 100
    # Fall time
    tf = 10

    if i2cFreq > 400000:
        # Fm+ (Fast mode plus)
        trmax = 120
        tfmax = 120
        tsuDATmin = 50
        thdDATmin = 0
        tHIGHmin = 260
        tLOWmin = 500
    else:
        # Fm (Fast mode)
        trmax = 300
        tfmax = 300
        tsuDATmin = 100
        thdDATmin = 0
        tHIGHmin = 600
        tLOWmin = 1300
    
    # Convert pclkFreq into nsec
    tI2cclk = 1000000000 / pclkFreq

    # Convert target i2cFreq into cycle time (nsec)
    tSCL = 1000000000 / i2cFreq

    SCLDELmin = (trmax + tsuDATmin) / ((presc + 1) * tI2cclk) - 1
    SDADELmin = (tfmax + thdDATmin - tAFmin - ((dfcoeff + 3) * tI2cclk)) / ((presc + 1) * tI2cclk)

    tsync1 = tf + tAFmin + dfcoeff * tI2cclk + 2 * tI2cclk
    tsync2 = tr + tAFmin + dfcoeff * tI2cclk + 2 * tI2cclk

    tSCLH = tHIGHmin * tSCL / (tHIGHmin + tLOWmin) - tsync2
    tSCLL = tSCL - tSCLH - tsync1 - tsync2

    SCLH = tSCLH / ((presc + 1) * tI2cclk) - 1
    SCLL = tSCLL / ((presc + 1) * tI2cclk) - 1

    while (tsync1 + tsync2 + ((SCLH + 1) + (SCLL + 1)) * ((presc + 1) * tI2cclk) < tSCL):
        SCLH += 1

    global scldel
    global sdadel
    global sclh
    global scll

    scldel = int(SCLDELmin)
    sdadel = int(SDADELmin)
    sclh = int(SCLH)
    scll = int(SCLL)

def i2cClockTIMINGR(pclkFreq, i2cFreq, dfcoeff):
    for presc in range(15):
        i2cClockComputeRaw(pclkFreq=pclkFreq, i2cFreq=i2cFreq, presc=presc, dfcoeff=dfcoeff)

        global scldel
        global sdadel
        global sclh
        global scll

        if scldel < 16 and sdadel < 16 and sclh < 256 and scll < 256:
            i2cTimeR = (presc << 28) | (scldel << 20) | (sdadel << 16) | (sclh << 8) | (scll << 0)
            print("0x" + "{:08X}".format(i2cTimeR))
            break

i2cClockTIMINGR(pclkFreq=pclkFreq, i2cFreq=i2cFreq, dfcoeff=dfcoeff)