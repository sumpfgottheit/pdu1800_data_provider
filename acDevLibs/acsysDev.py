# Use acDevLibs for PyCharm Development from WarriorOfAvalon
# https://github.com/WarriorOfAvalon/AssettoCorsaDevLibs
"""
Feel free to do what you want with this :)

It is essentially a transcription of all of the functions within the ACSYS module to aid devs using IDE's

Turnemator13
"""

class aeroDec:
    CD = ""
    CL_Front = ""
    CL_Rear = ""


class csDec:
    AccG = ""
    Aero = ""
    BestLap = ""
    Brake = ""
    CGHeight = ""
    CamberDeg = ""
    CamberRad = ""
    Caster = ""
    Clutch = ""
    CurrentTyresCoreTemp = ""
    DY = ""
    DriftBestLap = ""
    DriftLastLap = ""
    DriftPoints = ""
    DriveTrainSpeed = ""
    DynamicPressure = ""
    Gas = ""
    Gear = ""
    InstantDrift = ""
    IsDriftInvalid = ""
    IsEngineLimiterOn = ""
    LapCount = ""
    LapInvalidated = ""
    LapTime = ""
    LastFF = ""
    LastLap = ""
    LastTyresTemp = ""
    Load = ""
    LocalAngularVelocity = ""
    LocalVelocity = ""
    Mz = ""
    NdSlip = ""
    NormalizedSplinePosition = ""
    PerformanceMeter = ""
    RPM = ""
    RideHeight = ""
    SlipAngle = ""
    SlipAngleContactPatch = ""
    SlipRatio = ""
    SpeedKMH = ""
    SpeedMPH = ""
    SpeedMS = ""
    SpeedTotal = ""
    Steer = ""
    SuspensionTravel = ""
    ToeInDeg = ""
    TurboBoost = ""
    TyreContactNormal = ""
    TyreContactPoint = ""
    TyreDirtyLevel = ""
    TyreHeadingVector = ""
    TyreLoadedRadius = ""
    TyreRadius = ""
    TyreRightVector = ""
    TyreSlip = ""
    TyreSurfaceDef = ""
    TyreVelocity = ""
    Velocity = ""
    WheelAngularSpeed = ""
    WorldPosition = ""


class glDec:
    LineStrip = ""
    Lines = ""
    Quads = ""
    Triangles = ""


class vecDec:
    def normalize(self, vector):
        return 0


class wheelsDec:
    FL = ""
    FR = ""
    RL = ""
    RR = ""


class acsysDec:
    AERO = aeroDec()
    CS = csDec()
    GL = glDec()
    Vec2f = vecDec()
    WHEELS = wheelsDec()

acsys = acsysDec()