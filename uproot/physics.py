#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import math

import uproot.rootio

# adheres to interface of https://github.com/scikit-hep/scikit-hep/blob/master/skhep/math/vectors.py

class TVector3Methods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.fX = x
        self.fY = y
        self.fZ = z

    @classmethod
    def origin(cls):
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def frompoint(cls, x, y, z):
        return cls(x, y, z)

    @classmethod
    def fromvector(cls, other):
        return cls(other.x, other.y, other.z)

    @classmethod
    def fromsphericalcoords(cls, r, theta, phi):
        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.sin(phi)
        z = r * math.cos(theta)
        return cls(x, y, z)

    @classmethod
    def fromcylindricalcoords(cls, rho, phi, z):
        x = rho * math.cos(phi)
        y = rho * math.sin(phi)
        z = z
        return cls(x, y, z)

    @classmethod
    def fromiterable(cls, values):
        x, y, z = values
        return cls(x, y, z)

    @property
    def x(self):
        return self.fX

    @x.setter
    def x(self, value):
        self.fX = value

    @property
    def y(self):
        return self.fY

    @y.setter
    def y(self, value):
        self.fY = value

    @property
    def z(self):
        return self.fZ

    @z.setter
    def z(self, value):
        self.fZ = value

    @property
    def rho(self):
        return math.sqrt(self.fX**2 + self.fY**2)

    @property
    def r(self):
        return math.sqrt(self.fX**2 + self.fY**2 + self.fZ**2)

    def costheta(self):
        if self.fX == 0.0 and self.fY == 0.0 and self.fZ == 0.0:
            return 1.0
        else:
            return self.fZ / math.sqrt(self.fX**2 + self.fY**2 + self.fZ**2)

    def theta(self, deg=False):
        theta = math.acos(self.costheta())
        return theta if not deg else math.degrees(theta)

    def phi(self, deg=False):
        phi = math.atan2(self.fY, self.fX)
        return phi if not deg else math.degrees(phi)

    def set(self, x, y, z):
        self.fX = x
        self.fY = y
        self.fZ = z

    def __setitem__(self, i, value):
        if i < 0:
            i += 3
        if i == 0:
            self.fX = value
        elif i == 1:
            self.fY = value
        elif i == 2:
            self.fZ = value
        else:
            raise IndexError("TVector3 is of length 3 only!")

    def __getitem__(self, i):
        if i < 0:
            i += 3
        if i == 0:
            return self.fX
        elif i == 1:
            return self.fY
        elif i == 2:
            return self.fZ
        else:
            raise IndexError("TVector3 is of length 3 only!")

    def tolist(self):
        return [self.fX, self.fY, self.fZ]

    def __len__(self):
        return 3

    @property
    def mag(self):
        return math.sqrt(self.fX**2 + self.fY**2 + self.fZ**2)

    @property
    def mag2(self):
        return self.fX**2 + self.fY**2 + self.fZ**2

    def __abs__(self):
        return math.sqrt(self.fX**2 + self.fY**2 + self.fZ**2)

    def copy(self):
        return TVector3(self.fX, self.fY, self.fZ)

    def unit(self):
        mag = self.mag
        if mag != 0.0 and mag != 1.0:
            return TVector3(self.fX / mag, self.fY / mag, self.fZ / mag)
        else:
            return self

    def __iadd__(self, other):
        self.fX += other.fX
        self.fY += other.fY
        self.fZ += other.fZ
        return self

    def __isub__(self, other):
        self.fX -= other.fX
        self.fY -= other.fY
        self.fZ -= other.fZ
        return self

    def __add__(self, other):
        return TVector3(self.fX + other.fX, self.fY + other.fY, self.fZ + other.fZ)

    def __sub__(self, other):
        return TVector3(self.fX - other.fX, self.fY - other.fY, self.fZ - other.fZ)

    def __imul__(self, scalar):
        self.fX *= scalar
        self.fY *= scalar
        self.fZ *= scalar
        return self

    def __mul__(self, scalar):
        return TVector3(self.fX * scalar, self.fY * scalar, self.fZ * scalar)

    def __rmul__(self, scalar):
        return TVector3(self.fX * scalar, self.fY * scalar, self.fZ * scalar)

    def __itruediv__(self, scalar):
        self.fX /= float(scalar)
        self.fY /= float(scalar)
        self.fZ /= float(scalar)

    __idiv__ = __itruediv__

    def __eq__(self, other):
        if other == 0.0:
            return self.fX == 0.0 and self.fY == 0.0 and self.fZ == 0.0
        else:
            return self.fX == other.fX and self.fY == other.fY and self.fZ == other.fZ

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.fX == 0.0 and self.fY == 0.0 and self.fZ == 0.0

    def __iter__(self):
        return (self.fX, self.fY, self.fZ).__iter__()

    def dot(self, other):
        return self.fX*other.fX + self.fY*other.fY + self.fZ*other.fZ

    def cross(self, other):
        return TVector3(self.fY * other.fZ - self.fZ * other.fY,
                        self.fZ * other.fX - self.fX * other.fZ,
                        self.fX * other.fY - self.fY * other.fX)

    def rotate(self, angle, *args):
        if len(args) == 1 and isinstance(args[0], Vector3D):
            ux, uy, uz = args[0].fX, args[0].fY, args[0].fZ
        elif len(args) == 1 and len(args[0]) == 3:
            ux, uy, uz = args[0]
        elif len(args) == 3:
            ux, uy, uz = args
        else:
            raise TypeError("Input object not a Vector3D nor an iterable with 3 elements.")

        norm = math.sqrt(ux**2 + uy**2 + uz**2)
        if norm != 1.0:
            ux = ux / norm
            uy = uy / norm
            uz = uz / norm
        c = math.cos(angle)
        s = math.sin(angle)
        c1 = 1.0 - c

        xp = (c + ux**2 * c1) * self.fX + (ux * uy * c1 - uz * s) * self.fY + (ux * uz * c1 + uy * s) * self.fZ
        yp = (ux * uy * c1 + uz * s) * self.fX + (c + uy**2 * c1) * self.fY + (uy * uz * c1 - ux * s) * self.fZ
        zp = (ux * uz * c1 - uy * s) * self.fX + (uy * uz * c1 + ux * s) * self.fY + (c + uz**2 * c1) * self.fZ

        return TVector3(xp, yp, zp)

    def rotatex(self, angle):
        return self.rotate(angle, 1, 0, 0)

    def rotatey(self, angle):
        return self.rotate(angle, 0, 1, 0)

    def rotatez(self, angle):
        return self.rotate(angle, 0, 0, 1)

    def cosdelta(self, other):
        m1 = self.mag2
        m2 = other.mag2
        if m1 == 0.0 or m2 == 0.0:
            return 1.0
        r = self.dot(other) / math.sqrt(m1 * m2)
        return max(-1.0, min(1.0, r))

    def angle(self, other, deg=False):
        cd = self.cosdelta(other)
        return math.acos(cd) if not deg else math.degrees(math.acos(cd))

    def isparallel(self, other):
        return self.cosdelta(other) == 1.0

    def isantiparallel(self, other):
        return self.cosdelta(other) == -1.0

    def iscollinear(self, other):
        return abs(self.cosdelta(other)) == 1.0

    def isopposite(self, other):
        return (self + other) == 0

    def isperpendicular(self, other):
        return self.dot(other) == 0

    def __repr__(self):
        return "TVector3({0}, {1}, {2})".format(self.fX, self.fY, self.fZ)

    def __str__(self):
        return str((self.fX, self.fY, self.fZ))
        
# uproot.rootio.methods["TVector3"] = TVector3Methods

class TLorentzVectorMethods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __init__(self, x=0.0, y=0.0, z=0.0, t=0.0):
        self.fP = TVector3(x, y, z)
        self.fE = t

    @classmethod
    def from4vector(cls, other):
        return cls(other.fP.fX, other.fP.fY, other.fP.fZ, other.fE)

    @classmethod
    def from3vector(cls, other, t):
        return cls(other.fX, other.fY, other.fZ, t)

    @classmethod
    def fromiterable(cls, values):
        x, y, z, t = values
        return cls(x, y, z, t)


        
# uproot.rootio.methods["TLorentzVector"] = TLorentzVectorMethods
