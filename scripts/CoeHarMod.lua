-- CoeHarMod Lua 脚本
-- 依赖 UncivCN 的 Lua 模组系统（TriggerLuaFunction / Lua 条件 <if [...] returns true>）

--[[
	将军/海军统帅光环：指挥等级（Resource.AuxiliaryCounter2，由 Culture.General/Admiral 政策提供）
	决定光环覆盖的单位时代范围。等价于原先每时代一条的
	"[+X]% Strength bonus for [{Era.T} {Military} {Land}] units within [R] tiles <when above [T-1] [Resource.AuxiliaryCounter2]>"
	写法：单位时代序号 <= 指挥等级 即获得加成。
]]
function auraCoversUnitEra(ctx)
	local u = ctx.unit
	local civ = ctx.civ
	if not u or not civ then return false end
	local level = civ.getResourceAmount("Resource.AuxiliaryCounter2")
	return u.getEraNumber() <= level
end

--[[
	AI 修正：市政自动解锁。
	等价于原先 GlobalUniques 中 60 条
	"Discover [Civic.X] <upon entering the [Era.Y]> <for [AI player] Civilizations>"
	在每回合开始时，把当前时代及以前时代的市政全部解锁（discoverTech 幂等，已研究则忽略）。
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

function aiUnlockCivics(ctx)
	local civ = ctx.civ
	if not civ then return false end
	local era = civ.getEraNumber()
	for e, civics in pairs(civicsByEra) do
		if e <= era then
			for _, name in ipairs(civics) do
				civ.discoverTech(name)
			end
		end
	end
	return true
end

--[[
	AI 修正：每回合补齐战略资源与政策槽。
	等价于原先 GlobalUniques 中 11 条
	"Provides [N] [Resource.X] <for [AI player] Civilizations>"
]]
function aiProvideResources(ctx)
	local civ = ctx.civ
	if not civ then return false end
	civ.addResource("Resource.Horse", 10)
	civ.addResource("Resource.Iron", 10)
	civ.addResource("Resource.Niter", 10)
	civ.addResource("Resource.Coal", 10)
	civ.addResource("Resource.Oil", 10)
	civ.addResource("Resource.Aluminum", 10)
	civ.addResource("Resource.Uranium", 10)
	civ.addResource("Resource.MilitaryPolicySlot", 65535)
	civ.addResource("Resource.EconomicPolicySlot", 65535)
	civ.addResource("Resource.DiplomaticPolicySlot", 65535)
	civ.addResource("Resource.GenericPolicySlot", 65535)
	return true
end
