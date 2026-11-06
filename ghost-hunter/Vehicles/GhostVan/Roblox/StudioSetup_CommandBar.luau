-- GhostVan one-time Studio setup. Paste into the Studio COMMAND BAR (View > Command Bar) with the imported
-- GhostVan model selected. These properties can only be set in Studio, not by game scripts:
--   * CollisionFidelity (the hollow body needs PreciseConvexDecomposition so players can walk inside)
--   * SurfaceAppearance texture maps (fill the rbxassetid numbers in GhostVanConfig.TextureSets first)
local model = game:GetService("Selection"):Get()[1]
assert(model and model:IsA("Model"), "Select the GhostVan model first")
local Config = require(model:FindFirstChild("GhostVanConfig", true))

local fidelity = {
	Body = Enum.CollisionFidelity.PreciseConvexDecomposition,
	Interior = Enum.CollisionFidelity.PreciseConvexDecomposition,
	FrontDoorL = Enum.CollisionFidelity.Hull, FrontDoorR = Enum.CollisionFidelity.Hull,
	RearDoorL = Enum.CollisionFidelity.Hull, RearDoorR = Enum.CollisionFidelity.Hull,
	SlidingDoor = Enum.CollisionFidelity.Box, Glass = Enum.CollisionFidelity.Hull,
	FrontDoorLGlass = Enum.CollisionFidelity.Box, FrontDoorRGlass = Enum.CollisionFidelity.Box,
	RearDoorLGlass = Enum.CollisionFidelity.Box, RearDoorRGlass = Enum.CollisionFidelity.Box,
	Wheel_FL = Enum.CollisionFidelity.Hull, Wheel_FR = Enum.CollisionFidelity.Hull,
	Wheel_RL = Enum.CollisionFidelity.Hull, Wheel_RR = Enum.CollisionFidelity.Hull,
}
for name, f in fidelity do
	local p = model:FindFirstChild(name, true)
	if p and p:IsA("MeshPart") then
		p.CollisionFidelity = f
	end
end

for setName, set in Config.TextureSets do
	if set.ColorMap == "rbxassetid://0" then
		warn("GhostVan: fill the asset ids for texture set " .. setName .. " in GhostVanConfig")
		continue
	end
	for _, name in set.Parts do
		local p = model:FindFirstChild(name, true)
		if p and p:IsA("MeshPart") then
			local sa = p:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
			sa.ColorMap = set.ColorMap
			sa.NormalMap = set.NormalMap
			sa.RoughnessMap = set.RoughnessMap
			sa.MetalnessMap = set.MetalnessMap
			sa.Parent = p
		end
	end
end
print("GhostVan setup done")
