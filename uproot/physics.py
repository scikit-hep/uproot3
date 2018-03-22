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

def vector3(x, y, z):
    return TVector3Methods(x, y, z)

def spherical3(r, theta, phi):
    return TVector3Methods.fromsphericalcoords(r, theta, phi)

def cylindrical3(rho, phi, z):
    return TVector3Methods.fromcylindricalcoords(rho, phi, z)

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
        if self.fX == 0 and self.fY == 0 and self.fZ == 0:
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
        return self.__class__(self.fX, self.fY, self.fZ)

    def unit(self):
        mag = self.mag
        if mag != 0 and mag != 1:
            return self.__class__(self.fX / mag, self.fY / mag, self.fZ / mag)
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
        return self.__class__(self.fX + other.fX, self.fY + other.fY, self.fZ + other.fZ)

    def __sub__(self, other):
        return self.__class__(self.fX - other.fX, self.fY - other.fY, self.fZ - other.fZ)

    def __imul__(self, other):
        self.fX *= scalar
        self.fY *= scalar
        self.fZ *= scalar
        return self

    def __mul__(self, other):
        if isinstance(other, TVector3Methods):
            return self.dot(other)
        else:
            return self.__class__(self.fX * other, self.fY * other, self.fZ * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, scalar):
        self.fX /= float(scalar)
        self.fY /= float(scalar)
        self.fZ /= float(scalar)
        return self

    __idiv__ = __itruediv__

    def __truediv__(self, scalar):
        return self.__class__(self.fX / scalar, self.fY / scalar, self.fZ / scalar)

    __div__ = __truediv__

    def __eq__(self, other):
        if other == 0:
            return self.fX == 0 and self.fY == 0 and self.fZ == 0
        else:
            return self.fX == other.fX and self.fY == other.fY and self.fZ == other.fZ

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.fX == 0 and self.fY == 0 and self.fZ == 0

    def __iter__(self):
        return (self.fX, self.fY, self.fZ).__iter__()

    def dot(self, other):
        return self.fX*other.fX + self.fY*other.fY + self.fZ*other.fZ

    def cross(self, other):
        return self.__class__(self.fY * other.fZ - self.fZ * other.fY,
                              self.fZ * other.fX - self.fX * other.fZ,
                              self.fX * other.fY - self.fY * other.fX)

    def rotate(self, angle, *args):
        if len(args) == 1 and isinstance(args[0], TVector3Methods):
            ux, uy, uz = args[0].fX, args[0].fY, args[0].fZ
        elif len(args) == 1 and len(args[0]) == 3:
            ux, uy, uz = args[0]
        elif len(args) == 3:
            ux, uy, uz = args
        else:
            raise TypeError("Input object not a TVector3 nor an iterable with 3 elements.")

        norm = math.sqrt(ux**2 + uy**2 + uz**2)
        if norm != 1:
            ux = ux / norm
            uy = uy / norm
            uz = uz / norm
        c = math.cos(angle)
        s = math.sin(angle)
        c1 = 1.0 - c

        xp = (c + ux**2 * c1) * self.fX + (ux * uy * c1 - uz * s) * self.fY + (ux * uz * c1 + uy * s) * self.fZ
        yp = (ux * uy * c1 + uz * s) * self.fX + (c + uy**2 * c1) * self.fY + (uy * uz * c1 - ux * s) * self.fZ
        zp = (ux * uz * c1 - uy * s) * self.fX + (uy * uz * c1 + ux * s) * self.fY + (c + uz**2 * c1) * self.fZ

        return self.__class__(xp, yp, zp)

    def rotatex(self, angle):
        return self.rotate(angle, 1, 0, 0)

    def rotatey(self, angle):
        return self.rotate(angle, 0, 1, 0)

    def rotatez(self, angle):
        return self.rotate(angle, 0, 0, 1)

    def cosdelta(self, other):
        m1 = self.mag2
        m2 = other.mag2
        if m1 == 0 or m2 == 0:
            return 1.0
        r = self.dot(other) / math.sqrt(m1 * m2)
        return max(-1.0, min(1.0, r))

    def angle(self, other, deg=False):
        cd = self.cosdelta(other)
        return math.acos(cd) if not deg else math.degrees(math.acos(cd))

    def isparallel(self, other):
        return self.cosdelta(other) == 1

    def isantiparallel(self, other):
        return self.cosdelta(other) == -1

    def iscollinear(self, other):
        return abs(self.cosdelta(other)) == 1

    def isopposite(self, other):
        return (self + other) == 0

    def isperpendicular(self, other):
        return self.dot(other) == 0

    def __repr__(self):
        return "{0}({1:.4g}, {2:.4g}, {3:.4g})".format(self.__class__.__name__, self.fX, self.fY, self.fZ)

    def __str__(self):
        return str((self.fX, self.fY, self.fZ))
        
uproot.rootio.methods["TVector3"] = TVector3Methods

def vector4(x, y, z, t):
    return TLorentzVectorMethods(x, y, z, t)

def spherical4(r, theta, phi, t):
    return TLorentzVectorMethods.from3vector(TVector3Methods.fromsphericalcoords(r, theta, phi), t)

def cylindrical4(rho, phi, z, t):
    return TLorentzVectorMethods.from3vector(TVector3Methods.fromcylindricalcoords(rho, phi, z), t)

def pxpypze(px, py, pz, e):
    return vector4(px, py, pz, e)

def pxpypzm(px, py, pz, m):
    if m > 0:
        e = math.sqrt(px**2 + py**2 + pz**2 + m**2)
    else:
        e = math.sqrt(px**2 + py**2 + pz**2 - m**2)
    return pxpypze(px, py, pz, e)

def ptetaphie(pt, eta, phi, e):
    px = pt*math.cos(phi)
    py = pt*math.sin(phi)
    pz = pt*math.sinh(eta)
    return pxpypze(px, py, pz, e)

def ptetaphim(pt, eta, phi, m):
    px = pt*math.cos(phi)
    py = pt*math.sin(phi)
    pz = pt*math.sinh(eta)
    return pxpypzm(px, py, pz, m)

class TLorentzVectorMethods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __init__(self, x=0.0, y=0.0, z=0.0, t=0.0):
        self.fP = TVector3Methods(x, y, z)
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

    @property
    def x(self):
        return self.fP.fX

    @x.setter
    def x(self, value):
        self.fP.fX = value

    @property
    def y(self):
        return self.fP.fY

    @y.setter
    def y(self, value):
        self.fP.fY = value

    @property
    def z(self):
        return self.fP.fZ

    @z.setter
    def z(self, value):
        self.fP.fZ = value

    @property
    def vector(self):
        return self.fP.copy()

    @property
    def t(self):
        return self.fE

    @t.setter
    def t(self, value):
        self.fE = value

    def costheta(self):
        return self.fP.costheta()

    def theta(self, deg=False):
        return self.fP.theta(deg)

    def phi(self, deg=False):
        return self.fP.phi(deg)

    @property
    def px(self):
        return self.fP.fX

    @px.setter
    def px(self, value):
        self.fP.fX = value

    @property
    def py(self):
        return self.fP.fY

    @py.setter
    def py(self, value):
        self.fP.fY = value

    @property
    def pz(self):
        return self.fP.fZ

    @pz.setter
    def pz(self, value):
        self.fP.fZ = value

    @property
    def e(self):
        return self.fE

    @e.setter
    def e(self, value):
        self.fE = value

    def set(self, x, y, z, t):
        self.fP.fX = x
        self.fP.fY = y
        self.fP.fZ = z
        self.fE = t

    def setpxpypzm(self, px, py, pz, m):
        self.fP.set(px, py, pz)
        if m > 0:
            self.fE = math.sqrt(px**2 + py**2 + pz**2 + m**2)
        else:
            self.fE = math.sqrt(px**2 + py**2 + pz**2 - m**2)

    def setpxpypze(self, px, py, pz, e):
        self.set(px, py, pz, e)

    def setptetaphim(self, pt, eta, phi, m):
        px = pt*math.cos(phi)
        py = pt*math.sin(phi)
        pz = pt*math.sinh(eta)
        self.setpxpypzm(px, py, pz, m)

    def setptetaphie(self, pt, eta, phi, e):
        px = pt*math.cos(phi)
        py = pt*math.sin(phi)
        pz = pt*math.sinh(eta)
        self.setpxpypze(px, py, pz, e)

    def tolist(self):
        return [self.fP.fX, self.fP.fY, self.fP.fZ, self.fE]

    def __setitem__(self, i, value):
        if i < 0:
            i += 4
        if i == 0:
            self.fP.fX = value
        elif i == 1:
            self.fP.fY = value
        elif i == 2:
            self.fP.fZ = value
        elif i == 3:
            self.fE = value
        else:
            raise IndexError("TLorentzVector is of length 4 only!")

    def __getitem__(self, i):
        if i < 0:
            i += 4
        if i == 0:
            return self.fP.fX
        elif i == 1:
            return self.fP.fY
        elif i == 2:
            return self.fP.fZ
        elif i == 3:
            return self.fE
        else:
            raise IndexError("TLorentzVector is of length 3 only!")

    def __len__(self):
        return 4

    @property
    def p(self):
        return self.fP.mag

    @property
    def pt(self):
        return self.fP.rho

    @property
    def et(self):
        return float(self.fE) * self.pt / self.p

    @property
    def m(self):
        return self.mag

    @property
    def m2(self):
        return self.mag2

    @property
    def mass(self):
        return self.mag

    @property
    def mass2(self):
        return self.mag2

    @property
    def mt(self):
        return self.transversemass

    @property
    def mt2(self):
        return self.transversemass2

    @property
    def transversemass(self):
        mt2 = self.transversemass2
        return math.sqrt(mt2) if mt2 >= 0 else -math.sqrt(-mt2)

    @property
    def transversemass2(self):
        return self.fE**2 - self.fP.fZ**2

    @property
    def beta(self):
        return self.fP.mag / self.fE

    @property
    def gamma(self):
        beta = self.beta
        if beta < 1:
            return 1.0 / math.sqrt(1.0 - beta**2)
        else:
            return float("inf")

    @property
    def eta(self):
        return self.pseudorapidity

    @property
    def boostvector(self):
        return self.fP.__class__(self.fP.fX / self.fE, self.fP.fY / self.fE, self.fP.fZ / self.fE)

    @property
    def pseudorapidity(self):
        costheta = self.costheta()
        if abs(costheta) < 1:
            return -0.5 * math.log((1.0 - costheta) / (1.0 + costheta))
        else:
            return float("inf") if self.z > 0 else float("-inf")

    @property
    def rapidity(self):
        return 0.5 * math.log((self.fE + self.fP.fZ) / (self.fE - self.fP.fZ))

    @property
    def mag(self):
        mag2 = self.mag2
        return math.sqrt(mag2) if mag2 >= 0 else -math.sqrt(-mag2)

    @property
    def mag2(self):
        return self.fE**2 - self.fP.mag2

    @property
    def perp2(self):
        return self.fP.fX**2 + self.fP.fY**2

    @property
    def perp(self):
        return math.sqrt(self.perp2)

    def copy(self):
        return self.__class__(self.fP.fX, self.fP.fY, self.fP.fZ, self.fE)

    def __iadd__(self, other):
        self.fP += other.fP
        self.fE += other.fE
        return self

    def __isub__(self, other):
        self.fP -= other.fP
        self.fE -= other.fE
        return self

    def __add__(self, other):
        return self.__class__(self.fP.fX + other.fP.fX, self.fP.fY + other.fP.fY, self.fP.fZ + other.fP.fZ, self.fE + other.fE)

    def __sub__(self, other):
        return self.__class__(self.fP.fX - other.fP.fX, self.fP.fY - other.fP.fY, self.fP.fZ - other.fP.fZ, self.fE - other.fE)

    def __imul__(self, scalar):
        self.fP *= scalar
        self.fE *= scalar
        return self

    def __mul__(self, other):
        if isinstance(other, TLorentzVectorMethods):
            return self.dot(other)
        else:
            return self.__class__(self.fP.fX * other, self.fP.fY * other, self.fP.fZ * other, self.fE * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, scalar):
        self.fP.fX /= float(scalar)
        self.fP.fY /= float(scalar)
        self.fP.fZ /= float(scalar)
        self.fE /= float(scalar)
        return self

    __idiv__ = __itruediv__

    def __truediv__(self, scalar):
        return self.__class__(self.fP.fX / scalar, self.fP.fY / scalar, self.fP.fZ / scalar, self.fE / scalar)

    __div__ = __truediv__

    def __eq__(self, other):
        if other == 0:
            return self.fP.fX == 0 and self.fP.fY == 0 and self.fP.fZ == 0 and self.fE == 0
        else:
            return self.fP.fX == other.fP.fX and self.fP.fY == other.fP.fY and self.fP.fZ == other.fP.fZ and self.fE == other.fE

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        return (self.fP.fX, self.fP.fY, self.fP.fZ, self.fE).__iter__()

    def boost(self, *args):
        if len(args) == 1 and isinstance(args[0], TVector3Methods):
            bx, by, bz = args[0].fX, args[0].fY, args[0].fZ
        elif len(args) == 1 and len(args[0]) == 3:
            bx, by, bz = args[0]
        elif len(args) == 3:
            bx, by, bz = args
        else:
            raise TypeError("Input object not a TVector3 nor an iterable with 3 elements.")

        b2 = bx**2 + by**2 + bz**2
        gamma = 1.0 / math.sqrt(1.0 - b2)
        bp = bx * self.fP.fX + by * self.fP.fY + bz * self.fP.fZ
        if b2 > 0:
            gamma2 = (gamma - 1.0) / b2
        else:
            gamma2 = 0.0

        xp = self.fP.fX + gamma2 * bp * bx - gamma * bx * self.fE
        yp = self.fP.fY + gamma2 * bp * by - gamma * by * self.fE
        zp = self.fP.fZ + gamma2 * bp * bz - gamma * bz * self.fE
        tp = gamma * (self.fE - bp)

        return self.__class__(xp, yp, zp, tp)

    def rotate(self, angle, *args):
        v3p = self.fP.rotate(angle, *args)
        return self.__class__(v3p.fX, v3p.fY, v3p.fZ, self.fE)

    def rotatex(self, angle):
        return self.rotate(angle, 1, 0, 0)

    def rotatey(self, angle):
        return self.rotate(angle, 0, 1, 0)

    def rotatez(self, angle):
        return self.rotate(angle, 0, 0, 1)

    def dot(self, other):
        return self.fE*other.fE - self.fP.dot(other.fP)

    def deltaeta(self, other):
        return self.eta - other.eta

    def deltaphi(self, other):
        dphi = self.phi() - other.phi()
        while dphi > math.pi:
            dphi -= 2.0*math.pi
        while dphi < -math.pi:
            dphi += 2.0*math.pi
        return dphi

    def deltar(self, other):
        return math.sqrt(self.deltaeta(other)**2 + self.deltaphi(other)**2)

    def isspacelike(self):
        return self.mag2 < 0

    def istimelike(self):
        return self.mag2 > 0

    def islightlike(self):
        return self.mag2 == 0

    def __repr__(self):
        return "{0}({1:.4g}, {2:.4g}, {3:.4g}, {4:.4g})".format(self.__class__.__name__, self.fP.fX, self.fP.fY, self.fP.fZ, self.fE)

    def __str__(self):
        return str((self.fP.fX, self.fP.fY, self.fP.fZ, self.fE))

uproot.rootio.methods["TLorentzVector"] = TLorentzVectorMethods
