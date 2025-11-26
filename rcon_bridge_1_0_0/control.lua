-- control.lua
local json = require("json")

local function scan_entities()
    local entities_list = {}
    local surface = game.surfaces[1]
    
    -- Alle Entities finden (kannst mehrere types hinzufügen)
	local entities = surface.find_entities_filtered{
		position = {0, 0},  -- Spawn position (oder player position wenn jemand online)
		radius = 1000,  -- Scan Radius
		type = {
			"assembling-machine",
			"furnace",
			"mining-drill",
			"transport-belt",
			"underground-belt",
			"chemical-plant",
			"inserter",
			"boiler",
			"generator",
			"oil-refinery",
			"lab",
			"offshore-pump",
			"pipe",
			"pipe-to-ground",
			"electric-pole"
		}
	}
    
    for _, entity in pairs(entities) do
        local entity_data = {}
        
        -- BASIS DATEN (für alle)
        entity_data.machine_name = entity.name
        entity_data.x = entity.position.x
        entity_data.y = entity.position.y
		--entity_data.bounding_box = entity.bounding_box
        
        --Assembling Machine1
        if entity.name == "assembling-machine-1" then
			entity_data.status = entity.status or "None" --active state
			--entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
        end
		
		if entity.name == "oil-refinery" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"		
		end
		
		if entity.name == "chemical-plant" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"	
		end
		
		--Stone Furnace
        if entity.name == "furnace" then
			entity_data.status = entity.status or "None" --active state
			--entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
        end
		
		--Burner Miner
        if entity.type == "mining-drill" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
        end
		
		--Yellow Transport Belt
		if entity.type == "transport-belt" then
			--entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
		end
		
		--Yellow Transport Belt
		if entity.type == "underground-belt" then
			--entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
		end
		
		if entity.type == "inserter" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"	
		end
		
		if entity.name == "boiler" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"		
		end
		
		if entity.name == "steam-engine" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"		
		end
		
		if entity.name == "lab" then
			entity_data.status = entity.status or "None" --active state
			--entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"			
		end
		
		if entity.name == "offshore-pump" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"			
		end
		
		if entity.name == "pipe" then
			--entity_data.status = entity.status or "None" --active state
			--entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"			
		end
		
		if entity.name == "pipe-to-ground" then
			--entity_data.status = entity.status or "None" --active state
			--entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"			
		end
		
		if entity.type == "electric-pole" then
			--entity_data.status = entity.status or "None" --active state
			--entity_data.rotation = entity.direction or "None" --rotation
			--entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			--entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			--entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			--entity_data.products_finished = entity.products_finished or "None" --products finished
			--entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"			
		end
        
        table.insert(entities_list, entity_data)
    end
    
    return json.encode(entities_list)
end


local function scan_entities_boundingboxes()
	local entities_list = {}
    local surface = game.surfaces[1]
    
    -- Alle Entities finden (kannst mehrere types hinzufügen)
	local entities = surface.find_entities_filtered{
		position = {0, 0},  -- Spawn position (oder player position wenn jemand online)
		radius = 1000,  -- Scan Radius
		type = {
			"assembling-machine",
			"furnace",
			"mining-drill",
			"transport-belt",
			"underground-belt",
			"chemical-plant",
			"inserter",
			"boiler",
			"generator",
			"oil-refinery",
			"lab",
			"offshore-pump",
			"pipe",
			"pipe-to-ground",
			"electric-pole"
		}
	}
	
	for _, entity in pairs(entities) do
        local entity_data = {}
		
		entity_data.machine_name = entity.name
        entity_data.x = entity.position.x
        entity_data.y = entity.position.y
		entity_data.selection_box = entity.selection_box
		
		table.insert(entities_list, entity_data)
	end
	return json.encode(entities_list)
end

-- Neuer RCON Command für Assembler
commands.add_command("scan_entities", "Returns JSON list of assemblers", function(event)
    local json_str = scan_entities()
    if event.player_index == nil then
        rcon.print(json_str)
    else
        game.players[event.player_index].print(json_str)
    end
end)

-- Neuer RCON Command für Assembler
commands.add_command("scan_entities_boundingboxes", "Returns JSON list of assemblers", function(event)
    local json_str = scan_entities_boundingboxes()
    if event.player_index == nil then
        rcon.print(json_str)
    else
        game.players[event.player_index].print(json_str)
    end
end)