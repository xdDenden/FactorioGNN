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
			"electric-pole",
			"splitter"
		}
	}
    
    for _, entity in pairs(entities) do
        local entity_data = {}
        
        -- BASIS DATEN (für alle)
        entity_data.machine_name = entity.name
        entity_data.x = entity.position.x
        entity_data.y = entity.position.y
        
        --Assembling Machine1
        if entity.name == "assembling-machine-1" then
			entity_data.status = entity.status or "None" --active state
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
        end
		
		--Assembling Machine1
        if entity.name == "assembling-machine-2" then
			entity_data.status = entity.status or "None" --active state
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
        end
		
		--Assembling Machine1
        if entity.name == "assembling-machine-3" then
			entity_data.status = entity.status or "None" --active state
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
        end
		
		if entity.name == "oil-refinery" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe	
		end
		
		if entity.name == "chemical-plant" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
		end
		
		--Stone Furnace
        if entity.name == "stone-furnace" then
			entity_data.status = entity.status or "None" --active state
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
        end
		
		--Stone Furnace
        if entity.name == "steel-furnace" then
			entity_data.status = entity.status or "None" --active state
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.recipe_name = entity.get_recipe() and entity.get_recipe().name or "No Recipe" --recipe
			entity_data.is_crafting = entity.is_crafting() or "False" --is crafting?
			entity_data.products_finished = entity.products_finished or "None" --products finished
        end
		
		--Burner Miner
        if entity.type == "mining-drill" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
			entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
        end
		
		--Yellow Transport Belt
		if entity.type == "transport-belt" then
			entity_data.rotation = entity.direction or "None" --rotation
		end
		
		--Yellow Transport Belt
		if entity.type == "underground-belt" then
			entity_data.rotation = entity.direction or "None" --rotation
		end
		
		if entity.type == "inserter" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy
		end
		
		if entity.name == "boiler" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation	
		end
		
		if entity.name == "steam-engine" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation	
		end
		
		if entity.name == "lab" then
			entity_data.status = entity.status or "None" --active state
			entity_data.energy = (entity.energy == 0) and "False" or "True" --energy	
		end
		
		if entity.name == "offshore-pump" then
			entity_data.status = entity.status or "None" --active state
			entity_data.rotation = entity.direction or "None" --rotation		
		end
		
		if entity.name == "pipe" then		
		end
		
		if entity.name == "pipe-to-ground" then
			entity_data.rotation = entity.direction or "None" --rotation
		end
		
		if entity.type == "electric-pole" then		
		end
		
		if entity.type == "splitter" then
			entity_data.rotation = entity.direction or "None" --rotation
		end
        
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

-- Optional: Periodic logging
script.on_nth_tick(300, function()
    game.print("kys: " .. game.tick)
end)