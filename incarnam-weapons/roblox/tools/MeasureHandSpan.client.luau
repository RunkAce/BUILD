--[[
	MeasureHandSpan (temporary LocalScript - put it in StarterPlayerScripts, press Play, read Output)

	Plays each of YOUR animations on your R6 character and records the widest distance between the two
	chain eyelets, then prints the LinkCount the Warlink chain needs. Delete it afterwards.

	1. Paste your animation ids below.
	2. If the Warlink tool is in StarterPack, it is equipped automatically and the real "ChainEnd"
	   attachments are measured. Otherwise the R6 hands are measured plus EYELET_OFFSET.
]]
local ANIMATION_IDS = {
	-- "rbxassetid://1234567890",
}
local PITCH = 0.21 -- matches the exported ChainLink
local MARGIN = 0.05 -- 5% spare so the chain is just short of taut at the widest pose
local EYELET_OFFSET = 0.98 -- studs from the hand to the eyelet along the handle (Warlink cleaver)
local SAMPLE_HZ = 60

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid") :: Humanoid
local animator = humanoid:WaitForChild("Animator") :: Animator
assert(humanoid.RigType == Enum.HumanoidRigType.R6, "MeasureHandSpan: character is not R6")

-- equip Warlink if it is in the backpack
task.wait(1)
for _, t in player.Backpack:GetChildren() do
	if t:IsA("Tool") and (t:HasTag("Warlink") or t.Name:lower():find("warlink")) then
		humanoid:EquipTool(t)
		task.wait(0.5)
		break
	end
end

local function eyelets(): (Vector3, Vector3, string)
	local tool = character:FindFirstChildOfClass("Tool")
	if tool then
		local b = tool:FindFirstChild("Handle") and tool.Handle:FindFirstChild("ChainEnd")
		local a = tool:FindFirstChild("CleaverL") and tool.CleaverL:FindFirstChild("ChainEnd")
		if a and b then
			return (a :: Attachment).WorldPosition, (b :: Attachment).WorldPosition, "ChainEnd attachments"
		end
	end
	-- fallback: R6 hand points (RightGrip C0) pushed along the default handle direction
	local ra, la = character["Right Arm"] :: BasePart, character["Left Arm"] :: BasePart
	local hand = CFrame.new(0, -1, 0) * CFrame.Angles(-math.pi / 2, 0, 0)
	local r = (ra.CFrame * hand * CFrame.new(0, -EYELET_OFFSET, 0)).Position
	local l = (la.CFrame * hand * CFrame.new(0, -EYELET_OFFSET, 0)).Position
	return l, r, "R6 hands + EYELET_OFFSET"
end

local overall, overallName = 0, "idle"
do
	local a, b, how = eyelets()
	overall = (b - a).Magnitude
	print(string.format("[MeasureHandSpan] measuring %s; idle gap %.2f studs", how, overall))
end

for _, id in ANIMATION_IDS do
	local anim = Instance.new("Animation")
	anim.AnimationId = id
	local track = animator:LoadAnimation(anim)
	track.Priority = Enum.AnimationPriority.Action4
	track.Looped = false
	local waited = 0
	while track.Length == 0 and waited < 5 do
		waited += task.wait(0.1)
	end
	track:Play(0, 1, 1)
	local best = 0
	local t0 = os.clock()
	while track.IsPlaying or os.clock() - t0 < track.Length do
		local a, b = eyelets()
		best = math.max(best, (b - a).Magnitude)
		if os.clock() - t0 > track.Length + 0.25 then
			break
		end
		RunService.Heartbeat:Wait()
	end
	track:Stop(0)
	print(string.format("[MeasureHandSpan] %s  max eyelet gap %.2f studs (length %.2fs)", id, best, track.Length))
	if best > overall then
		overall, overallName = best, id
	end
	task.wait(0.3)
end

local links = math.ceil((overall * (1 + MARGIN)) / PITCH - 1e-9)
print(string.format("[MeasureHandSpan] WIDEST: %.2f studs (%s)  ->  set Tool attribute LinkCount = %d  (chain %.2f studs)",
	overall, overallName, links, links * PITCH))
