--!strict
-- AR_02 M4A1 - PIXELGATE factory_v1. Gameplay values are PROVISIONAL (tag: BALANCE_TBD), not real-world data.
-- Server is authoritative for ammo, cadence, damage and reload acceptance; the client only predicts presentation.
return {
	Id = "AR_02",
	DisplayName = "M4A1",
	Class = "AssaultRifle",
	Slot = "Primary",
	Variant = "factory_v1",

	-- virtual ammunition (BALANCE_TBD)
	Feed = "DetachableBoxMagazine",
	MagazineSize = 30,
	ReserveAmmo = 120,
	ChamberRound = true, -- tactical reload keeps +1 in the chamber
	FireModes = { "Auto", "Semi" },
	RateOfFire = 780, -- rounds per minute
	ReloadTactical = 2.0, -- seconds (matches the Reload_Tactical take)
	ReloadEmpty = 2.6, -- seconds (matches the Reload_Empty take: includes charging-handle release)
	Damage = { Base = 24, Headshot = 1.6, FalloffStart = 60, FalloffEnd = 140, FalloffMin = 0.7 },
	Spread = { Hip = 3.2, ADS = 0.35, MoveAdd = 1.8, PerShot = 0.18, Max = 6, RecoverPerSec = 9 },
	Recoil = { Vertical = 1.1, HorizontalJitter = 0.35, FirstShotMult = 1.3, ADSMult = 0.65, RecoverPerSec = 14 },
	ADSTime = 0.22,
	SprintToFire = 0.18,
	MoveSpeedMult = 0.94,

	-- rig contract (bone / attachment names inside AR_02_Viewmodel.fbx)
	Bones = { "Root", "Trigger", "Magazine", "ChargingHandle", "BoltCarrier", "DustCover", "Selector" },
	Attachments = { "GripRight", "RightHandIK", "GripLeft", "LeftHandIK", "Muzzle", "ADS", "Ejection", "MagazineSeat" },

	-- weapon-side animation takes in the FBX (hand/arm takes belong to the project's viewmodel arms)
	Animations = {
		Idle = "Idle",
		Fire = "Fire",
		DryFire = "DryFire",
		ReloadTactical = "Reload_Tactical",
		ReloadEmpty = "Reload_Empty",
		Inspect = "Inspect",
	},
	-- animation notify events, seconds from the start of each take. Ammo state may ONLY change at AmmoCommit;
	-- a reload cancelled before AmmoCommit leaves the magazine untouched.
	Events = {
		Fire = { Muzzle = 0.0, Eject = 0.05 },
		Reload_Tactical = { MagOut = 0.3, MagIn = 1.65, AmmoCommit = 1.7, End = 2.0 },
		Reload_Empty = { MagOut = 0.3, MagIn = 1.65, BoltRelease = 2.2, AmmoCommit = 2.25, End = 2.6 },
		Inspect = { End = 3.0 },
	},
	-- empty state: bolt carrier held back + dust cover open (pose = last frame of Fire with BoltCarrier at -0.2)
	EmptyPose = { BoltCarrier = -0.2, DustCover = -100 },

	-- cosmetics: future skins replace these maps; MaskMap R=Body G=Furniture B=MetalAccent RG=Magazine
	Textures = {
		Color = "AR_02_Factory_ColorMap.png",
		Normal = "AR_02_Factory_NormalMap.png",
		Roughness = "AR_02_Factory_RoughnessMap.png",
		Metalness = "AR_02_Factory_MetalnessMap.png",
		Mask = "AR_02_Factory_MaskMap.png",
	},
}
