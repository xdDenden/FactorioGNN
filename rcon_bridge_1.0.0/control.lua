-- control.lua
local json = require("json")

-- Funktion zum Sammeln der Daten
local function get_game_data()
    local players = {}
    for _, player in pairs(game.connected_players) do
        table.insert(players, {
            name = player.name,
            position = { x = player.position.x, y = player.position.y },
            online_time = player.online_time
        })
    end
    
    local data = {
        tick = game.tick,
        player_count = #game.connected_players,
        players = players
    }
    
    return json.encode(data)
end

local function scan_entities()
    local entities_list = {}
    local surface = game.surfaces[1]  -- Nauvis
    
    -- Alle Entities finden (kannst mehrere types hinzufügen)
	local entities = surface.find_entities_filtered{
		position = {0, 0},  -- Spawn position (oder player position wenn jemand online)
		radius = 100,  -- Scan Radius
		type = {"assembling-machine", "furnace", "mining-drill"}  -- Beispiel
	}
    
    for _, entity in pairs(entities) do
        local entity_data = {}
        
        -- BASIS DATEN (für alle)
        entity_data.machine_name = entity.name
        entity_data.x = entity.position.x
        entity_data.y = entity.position.y
        
        -- CHECK: Welcher Maschinen-Typ?
        if entity.type == "assembling-machine" then
            entity_data.type = "assembler"
            entity_data.rotation = entity.direction
            entity_data.status = entity.status
            entity_data.is_crafting = entity.is_crafting()
            
            if entity.get_recipe() then
                entity_data.recipe_name = entity.get_recipe().name
            end
            
            entity_data.energy = entity.energy
            entity_data.products_finished = entity.products_finished
            
        elseif entity.type == "furnace" then
            entity_data.type = "furnace"
            entity_data.is_crafting = entity.is_crafting()
            
            if entity.get_recipe() then
                entity_data.recipe_name = entity.get_recipe().name
            end
            
        elseif entity.type == "mining-drill" then
            entity_data.type = "drill"
            entity_data.mining_target = entity.mining_target and entity.mining_target.name or "none"
            entity_data.status = entity.status
            
        -- Hier kannst du mehr Types hinzufügen
        else
            entity_data.type = "unknown"
        end
        
        table.insert(entities_list, entity_data)
    end
    
    return json.encode(entities_list)
end

-- RCON Command registrieren
commands.add_command("get_info", "Returns JSON game info", function(event)
    local json_str = get_game_data()
    if event.player_index == nil then
        rcon.print(json_str)
    else
        game.players[event.player_index].print(json_str)
    end
end)

-- Neuer RCON Command für Assembler
commands.add_command("scan_assemblers", "Returns JSON list of assemblers", function(event)
    local json_str = scan_entities()
    if event.player_index == nil then
        rcon.print(json_str)
    else
        game.players[event.player_index].print(json_str)
    end
end)

-- Optional: Periodic logging
script.on_nth_tick(300, function()
    game.print("Game tick: " .. game.tick)
end)