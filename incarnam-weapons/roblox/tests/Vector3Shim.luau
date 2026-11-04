-- Minimal Roblox Vector3 stand-in for running pure modules outside Roblox (tests only).
local Vector3 = {}
local mt = {}

local function new(x: number?, y: number?, z: number?)
	return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0 }, mt)
end

local methods = {}
function methods.Dot(a, b)
	return a.X * b.X + a.Y * b.Y + a.Z * b.Z
end
function methods.Cross(a, b)
	return new(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X)
end
function methods.Lerp(a, b, t)
	return new(a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t, a.Z + (b.Z - a.Z) * t)
end

mt.__index = function(v, k)
	if k == "Magnitude" then
		return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
	elseif k == "Unit" then
		local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
		if m == 0 then
			return new(0, 0, 0)
		end
		return new(v.X / m, v.Y / m, v.Z / m)
	end
	return methods[k]
end
mt.__add = function(a, b)
	return new(a.X + b.X, a.Y + b.Y, a.Z + b.Z)
end
mt.__sub = function(a, b)
	return new(a.X - b.X, a.Y - b.Y, a.Z - b.Z)
end
mt.__mul = function(a, b)
	if type(a) == "number" then
		return new(b.X * a, b.Y * a, b.Z * a)
	elseif type(b) == "number" then
		return new(a.X * b, a.Y * b, a.Z * b)
	end
	return new(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end
mt.__div = function(a, b)
	if type(b) == "number" then
		return new(a.X / b, a.Y / b, a.Z / b)
	end
	return new(a.X / b.X, a.Y / b.Y, a.Z / b.Z)
end
mt.__unm = function(a)
	return new(-a.X, -a.Y, -a.Z)
end
mt.__tostring = function(v)
	return string.format("(%.3f, %.3f, %.3f)", v.X, v.Y, v.Z)
end

Vector3.new = new
return Vector3
