-- CoeHarMod Lua 脚本
-- 依赖 UncivCN 的 Lua 模组系统（TriggerLuaFunction / Lua 条件 <if [...] returns true>）

--[[
	将军/海军统帅光环。
	原 JSON 写法为每个伟人 9 条：
	"[+X]% Strength bonus for [{Era.T} {Military} {Land}] units within [R] tiles <when above [T-1] [Resource.AuxiliaryCounter2]>"
	设计意图：指挥等级（Resource.AuxiliaryCounter2，由 Culture.General/Admiral 政策提升）越高，
	光环能覆盖的单位时代越全 —— 即"单位时代序号 <= 指挥等级"即获得加成。
	合并为一条 Lua 条件后，数值/半径只改 JSON 一处，等级门槛逻辑全在脚本里。
]]
function AuraCoversUnitEra(ctx)
	local u = ctx.unit
	local civ = ctx.civ
	if not u or not civ then return false end
	return u.getEraNumber() <= civ.getVariable("AuxiliaryCounter2")
end

--[[
	AI 修正：市政自动解锁。
	原 JSON 写法为 60 条 "Discover [Civic.X] <upon entering the [Era.Y]> <for [AI player] Civilizations>"，
	设计意图：AI 进入新时代时获得该时代及以前的所有市政（一次性、增量）。
	用 ctx.store 记录每个 AI 已解锁的最高时代：每回合只做一次整数比较，
	仅在时代前进时增量解锁新增时代的市政（首次运行/老存档会一次性补齐到当前时代）。
]]
local civicsByEra = {
	[1] = { -- Era.Classical
		"Civic.Code", "Civic.Skill", "Civic.BasicTrade", "Civic.MilitaryTradition",
		"Civic.NationalLaborForce", "Civic.EarlyEmpire", "Civic.Mysticism"
	},
	[2] = { -- Era.Medieval
		"Civic.GamesAndEntertainment", "Civic.PoliticalPhilosophy", "Civic.DramaAndPoetry",
		"Civic.MilitaryTraining", "Civic.DefensiveTactics", "Civic.History", "Civic.Theology"
	},
	[3] = { -- Era.Renaissance
		"Civic.NavalTradition", "Civic.Feudalism", "Civic.Administration", "Civic.Mercenaries",
		"Civic.MedievalBazaar", "Civic.TheWorkersUnion", "Civic.DivinRightOfKings"
	},
	[4] = { -- Era.Industrial
		"Civic.Exploration", "Civic.Humanism", "Civic.ForeighService", "Civic.ReformedChurch",
		"Civic.Mercantilism", "Civic.Enlightenment"
	},
	[5] = { -- Era.Modern
		"Civic.Colonialism", "Civic.CivilEngineering", "Civic.Nationalism", "Civic.OperaAndBallet",
		"Civic.NaturalHistory", "Civic.Urbanization", "Civic.ScorchedEarthStrategy"
	},
	[6] = { -- Era.Atomic
		"Civic.EarthProtection", "Civic.MassMedia", "Civic.Mobilization", "Civic.Capitalism",
		"Civic.Ideology", "Civic.NuclearProgram", "Civic.RightToVote", "Civic.Tolalitarianism",
		"Civic.ClassStruggle"
	},
	[7] = { -- Era.Information
		"Civic.CulturalHeritage", "Civic.ColdWar", "Civic.ProfessionalSports",
		"Civic.EmergencyDeployment", "Civic.SpaceRace"
	},
	[8] = { -- Era.Near-future
		"Civic.Environmentalism", "Civic.Globalization", "Civic.SocialMedia",
		"Civic.Near-FutureGovernance", "Civic.PoliticalAdventures", "Civic.DecentralizedSovereighty",
		"Civic.OptimizationCommand", "Civic.GlobalWarmingMitigation", "Civic.SmartPowerFoctrine",
		"Civic.InformationWarfare", "Civic.NecessityExpedition", "Civic.CulturalHegemony"
	}
}

function AiUnlockCivics(ctx)
	local civ = ctx.civ
	if not civ then return false end
	local era = civ.getEraNumber()
	local key = "CoeHarMod:unlockedEra:" .. civ.id
	local last = tonumber(ctx.store.get(key, "-1")) or -1
	if era <= last then return true end
	for e = last + 1, era do
		local civics = civicsByEra[e]
		if civics then
			for _, name in ipairs(civics) do
				civ.discoverTech(name)
			end
		end
	end
	ctx.store.set(key, tostring(era))
	return true
end

--[[
	AI 修正：每回合补齐战略资源与政策槽。
	原 JSON 写法为 11 条 "Provides [N] [Resource.X] <for [AI player] Civilizations>"，
	设计意图：AI 不受战略资源与政策槽限制，始终有兵可造、有卡可买。
	数据表与逻辑分离：新增资源只需在表里加一行。
]]
local aiPerTurnResources = {
	"Resource.Horse", "Resource.Iron", "Resource.Niter", "Resource.Coal",
	"Resource.Oil", "Resource.Aluminum", "Resource.Uranium"
}
local aiPerTurnPolicySlots = {
	"Resource.MilitaryPolicySlot", "Resource.EconomicPolicySlot",
	"Resource.DiplomaticPolicySlot", "Resource.GenericPolicySlot"
}

function AiProvideResources(ctx)
	local civ = ctx.civ
	if not civ then return false end
	for _, r in ipairs(aiPerTurnResources) do civ.addResource(r, 10) end
	for _, s in ipairs(aiPerTurnPolicySlots) do civ.addResource(s, 65535) end
	return true
end
