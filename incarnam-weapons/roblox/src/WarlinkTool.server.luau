--[[
	WarlinkTool (Script inside the Warlink Tool)
	R6 only has a RIGHT grip. The Tool's Handle (right cleaver) is held by Roblox's RightGrip weld as
	usual; this script welds the second cleaver ("CleaverL") to the R6 "Left Arm" at the same hand
	offset, mirrored. Your animations move the arms, so both cleavers and both chain eyelets follow.

	If your animations already drive weapon parts with custom Motor6Ds (animated tool rig), skip this
	script and use your own joints: the chain only needs the two "ChainEnd" attachments.
	Author CleaverL next to the Handle in its stowed pose; that pose is kept while unequipped or dropped.
]]
local tool = script.Parent :: Tool
local handle = tool:WaitForChild("Handle") :: BasePart

-- R6 hand point and default tool orientation: same as RightGrip's C0 on the Right Arm.
-- CleaverL is already the mirrored mesh, so the left hand uses the same Grip (no extra rotation).
local HAND = CFrame.new(0, -1, 0) * CFrame.Angles(-math.pi / 2, 0, 0)

-- Stow weld: CleaverL rides with the Handle (in the backpack, when dropped, as a pickup) at the pose
-- it was authored in. Without it, an unequipped CleaverL is a loose part that falls out of the world.
local function getLeft(): BasePart?
	local p = tool:FindFirstChild("CleaverL")
	return if p and p:IsA("BasePart") then p else nil
end

local stow = handle:FindFirstChild("CleaverLStow") :: Weld?
do
	local left = getLeft()
	if left and not stow then
		local w = Instance.new("Weld")
		w.Name = "CleaverLStow"
		w.Part0 = handle
		w.Part1 = left
		w.C0 = handle.CFrame:ToObjectSpace(left.CFrame)
		w.Parent = handle
		stow = w
	end
	if left then
		left.Anchored = false
		left.CanCollide = false
		left.Massless = true
	end
end

local weld: Weld? = nil

local function cleanup()
	if weld then
		weld:Destroy()
		weld = nil
	end
	if stow then
		stow.Enabled = true
	end
end

tool.Equipped:Connect(function()
	cleanup()
	local character = tool.Parent
	local arm = character and character:FindFirstChild("Left Arm")
	local left = getLeft()
	if not (arm and arm:IsA("BasePart") and left) then
		warn("[WarlinkTool] Left Arm or CleaverL not found: this tool expects an R6 character")
		return
	end
	if stow then
		stow.Enabled = false -- hand it over to the left hand (avoids a closed joint loop through both arms)
	end
	local w = Instance.new("Weld")
	w.Name = "LeftGrip"
	w.Part0 = arm
	w.Part1 = left
	w.C0 = HAND
	w.C1 = tool.Grip
	w.Parent = arm
	weld = w
end)

tool.Unequipped:Connect(cleanup)
tool.Destroying:Connect(cleanup)
